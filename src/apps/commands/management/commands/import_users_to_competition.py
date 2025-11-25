import csv
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from competitions.models import Competition, CompetitionParticipant

User = get_user_model()


class Command(BaseCommand):
    help = "Import users from CSV and add them to a competition"

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str)
        parser.add_argument('--competition-id', type=int)
        parser.add_argument('--competition-secret-key', type=str)
        parser.add_argument('--status', type=str, default=CompetitionParticipant.APPROVED, choices=[
            CompetitionParticipant.UNKNOWN,
            CompetitionParticipant.DENIED,
            CompetitionParticipant.APPROVED,
            CompetitionParticipant.PENDING,
        ])
        parser.add_argument('--reset-password', action='store_true')
        parser.add_argument('--require-email', action='store_true')
        parser.add_argument('--update-email', action='store_true')
        parser.add_argument('--inactive', action='store_true')
        parser.add_argument('--set-active-existing', action='store_true')
        parser.add_argument('--set-inactive-existing', action='store_true')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        competition_id = options.get('competition_id')
        competition_secret_key = options.get('competition_secret_key')
        status = options['status']
        reset_password = options['reset_password']
        require_email = options['require_email']
        update_email = options['update_email']
        inactive = options['inactive']
        set_active_existing = options['set_active_existing']
        set_inactive_existing = options['set_inactive_existing']
        dry_run = options['dry_run']

        competition = None
        if competition_id:
            try:
                competition = Competition.objects.get(id=competition_id)
            except Competition.DoesNotExist:
                raise CommandError('Competition not found by id')
        elif competition_secret_key:
            try:
                competition = Competition.objects.get(secret_key=competition_secret_key)
            except Competition.DoesNotExist:
                raise CommandError('Competition not found by secret_key')
        else:
            raise CommandError('One of --competition-id or --competition-secret-key is required')

        created_users = 0
        updated_passwords = 0
        participants_created = 0
        participants_existing = 0
        emails_set = 0
        emails_updated = 0
        activated_existing = 0
        deactivated_existing = 0

        with open(csv_path, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)

        start_index = 0
        header = None
        if rows and rows[0]:
            maybe_header = [c.strip().lower() for c in rows[0]]
            if 'username' in maybe_header and 'password' in maybe_header:
                header = maybe_header
                start_index = 1

        with transaction.atomic():
            for row in rows[start_index:]:
                if not row:
                    continue
                if header:
                    data = {header[i]: (row[i].strip() if i < len(row) else '') for i in range(len(header))}
                    username = data.get('username', '')
                    password = data.get('password', '')
                    email = data.get('email', '')
                    is_active_csv = data.get('is_active', '')
                else:
                    if len(row) < 2:
                        continue
                    username = row[0].strip()
                    password = row[1].strip()
                    email = row[2].strip() if len(row) >= 3 else ''
                    is_active_csv = row[3].strip() if len(row) >= 4 else ''
                if not username or not password:
                    continue
                if require_email and not email:
                    continue
                is_active_val = None
                if is_active_csv:
                    v = is_active_csv.lower()
                    if v in ('true', '1', 'yes'):
                        is_active_val = True
                    elif v in ('false', '0', 'no'):
                        is_active_val = False
                user = User.objects.filter(username=username).first()
                if not user:
                    if dry_run:
                        created_users += 1
                        if email:
                            emails_set += 1
                        continue
                    try:
                        user = User.objects.create(username=username, is_active=(not inactive if is_active_val is None else is_active_val))
                        if email:
                            user.email = email
                        user.set_password(password)
                        user.save()
                        created_users += 1
                        if email:
                            emails_set += 1
                    except IntegrityError:
                        user = User.objects.get(username=username)
                else:
                    if reset_password and not dry_run:
                        user.set_password(password)
                        user.save()
                        updated_passwords += 1
                    if email and update_email and not dry_run:
                        if user.email != email:
                            user.email = email
                            user.save()
                            emails_updated += 1
                    if is_active_val is not None and not dry_run:
                        if user.is_active != is_active_val:
                            user.is_active = is_active_val
                            user.save()
                            if is_active_val:
                                activated_existing += 1
                            else:
                                deactivated_existing += 1
                    elif set_active_existing and not dry_run:
                        if not user.is_active:
                            user.is_active = True
                            user.save()
                            activated_existing += 1
                    elif set_inactive_existing and not dry_run:
                        if user.is_active:
                            user.is_active = False
                            user.save()
                            deactivated_existing += 1
                if dry_run:
                    continue
                try:
                    CompetitionParticipant.objects.create(user=user, competition=competition, status=status)
                    participants_created += 1
                except IntegrityError:
                    participants_existing += 1

        self.stdout.write(self.style.SUCCESS(
            f'users_created={created_users} passwords_updated={updated_passwords} participants_created={participants_created} participants_existing={participants_existing} emails_set={emails_set} emails_updated={emails_updated} activated_existing={activated_existing} deactivated_existing={deactivated_existing}'
        ))
