import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;

public class Main {

    public static void main(String[] args) throws IOException {
        if (args.length < 2) {
            throw new IllegalArgumentException("需要提供输入文件与输出文件路径，例如: java Main input.csv predictions.csv");
        }

        String inputPath = args[0];
        String outputPath = args[1];

        try (
            BufferedReader reader = new BufferedReader(new FileReader(inputPath));
            BufferedWriter writer = new BufferedWriter(new FileWriter(outputPath))
        ) {
            writer.write("id,sum");
            writer.newLine();

            // 跳过表头
            String line = reader.readLine();
            if (line == null) {
                throw new IOException("输入文件为空");
            }

            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length < 3) {
                    throw new IOException("数据格式错误，期望三列: " + line);
                }
                int id = Integer.parseInt(parts[0].trim());
                int a = Integer.parseInt(parts[1].trim());
                int b = Integer.parseInt(parts[2].trim());
                int sum = a + b;
                writer.write(id + "," + sum);
                writer.newLine();
            }
        }

        System.out.println("预测文件已生成: " + outputPath);
    }
}
