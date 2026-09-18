package agents;

import java.util.*;

/** Small strict JSON codec for local experiment records; no external parser dependency. */
final class PaperJson {
    private final String s; private int p;
    private PaperJson(String s){this.s=s;}
    static Object parse(String s){PaperJson j=new PaperJson(s);Object v=j.value();j.ws();if(j.p!=s.length())throw new IllegalArgumentException("Trailing JSON");return v;}
    private void ws(){while(p<s.length()&&Character.isWhitespace(s.charAt(p)))p++;}
    private char take(){if(p>=s.length())throw new IllegalArgumentException("Truncated JSON");return s.charAt(p++);}
    private Object value(){
        ws(); char c=s.charAt(p);
        if(c=='"')return string();
        if(c=='{'){p++;Map<String,Object> m=new LinkedHashMap<>();ws();if(s.charAt(p)=='}'){p++;return m;}while(true){ws();String k=string();ws();if(take()!=':')throw new IllegalArgumentException("Expected colon");if(m.put(k,value())!=null)throw new IllegalArgumentException("Duplicate key");ws();c=take();if(c=='}')return m;if(c!=',')throw new IllegalArgumentException("Expected comma");}}
        if(c=='['){p++;List<Object> a=new ArrayList<>();ws();if(s.charAt(p)==']'){p++;return a;}while(true){a.add(value());ws();c=take();if(c==']')return a;if(c!=',')throw new IllegalArgumentException("Expected comma");}}
        if(s.startsWith("true",p)){p+=4;return true;}if(s.startsWith("false",p)){p+=5;return false;}if(s.startsWith("null",p)){p+=4;return null;}
        int start=p;while(p<s.length()&&"-+0123456789.eE".indexOf(s.charAt(p))>=0)p++;
        String n=s.substring(start,p);if(n.isEmpty())throw new IllegalArgumentException("Invalid JSON");
        if(n.indexOf('.')>=0||n.indexOf('e')>=0||n.indexOf('E')>=0)return Double.valueOf(n);return Long.valueOf(n);
    }
    private String string(){if(take()!='"')throw new IllegalArgumentException("Expected string");StringBuilder b=new StringBuilder();while(true){char c=take();if(c=='"')return b.toString();if(c=='\\'){c=take();switch(c){case '"':case '\\':case '/':b.append(c);break;case 'n':b.append('\n');break;case 'r':b.append('\r');break;case 't':b.append('\t');break;case 'b':b.append('\b');break;case 'f':b.append('\f');break;case 'u':b.append((char)Integer.parseInt(s.substring(p,p+4),16));p+=4;break;default:throw new IllegalArgumentException("Invalid escape");}}else{if(c<32)throw new IllegalArgumentException("Control character");b.append(c);}}}
    static String write(Object v){
        if(v==null)return "null";
        if(v instanceof String){StringBuilder b=new StringBuilder("\"");for(char c:((String)v).toCharArray()){switch(c){case '"':b.append("\\\"");break;case '\\':b.append("\\\\");break;case '\n':b.append("\\n");break;case '\r':b.append("\\r");break;case '\t':b.append("\\t");break;default:if(c<32)b.append(String.format("\\u%04x",(int)c));else b.append(c);}}return b.append('"').toString();}
        if(v instanceof Number){if(!Double.isFinite(((Number)v).doubleValue()))throw new IllegalArgumentException("Nonfinite JSON");return v.toString();}
        if(v instanceof Boolean)return v.toString();
        if(v instanceof Map<?,?>){StringJoiner j=new StringJoiner(",","{","}");for(var e:((Map<?,?>)v).entrySet())j.add(write(e.getKey().toString())+":"+write(e.getValue()));return j.toString();}
        if(v instanceof Iterable<?>){StringJoiner j=new StringJoiner(",","[","]");for(Object e:(Iterable<?>)v)j.add(write(e));return j.toString();}
        throw new IllegalArgumentException("Unknown JSON value "+v.getClass());
    }
}
