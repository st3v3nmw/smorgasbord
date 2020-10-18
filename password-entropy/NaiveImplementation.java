import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.lang.Math;

class NaiveImplementation {
    public static void main(String[] args) {
        long symbol_space = 0;
        System.out.println("Tr0ub4dor&3 " + entropy("Tr0ub4dor&3"));
        System.out.println("qwER43@! " + entropy("qwER43@!"));
    }

    static double entropy(String s) {
        int symbol_space = (Pattern.compile("(?=.*[a-z])").matcher(s).find() ? 26 : 0);
        symbol_space += (Pattern.compile("(?=.*[A-Z])").matcher(s).find() ? 26 : 0);
        symbol_space += (Pattern.compile("(?=.*[0-9])").matcher(s).find() ? 10 : 0);
        symbol_space += (Pattern.compile("(?=.*[ !\"#$%&'()*+,-.\\/:;<=>?@\\[\\]^_`{|}~])").matcher(s).find() ? 33 : 0);
        return s.length() * Math.log(symbol_space) / Math.log(2);
    }
}