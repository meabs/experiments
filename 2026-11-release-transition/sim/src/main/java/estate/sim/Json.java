package estate.sim;

public class Json {
    public static String q(String s) {
        if (s == null) return "null";
        StringBuilder b = new StringBuilder("\"");
        for (char c : s.toCharArray()) {
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': break;
                case '\t': b.append(' '); break;
                default: if (c < 32) b.append(' '); else b.append(c);
            }
        }
        return b.append('"').toString();
    }
}
