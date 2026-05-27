package com.sipc.monitoringsystem.util;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.Base64;

public class Base64Util
{
    public static String inputStream2Base64(InputStream is) throws Exception {
        byte[] data = null;
        try {
            ByteArrayOutputStream swapStream = new ByteArrayOutputStream();
            byte[] buff = new byte[100];
            int rc = 0;
            while ((rc = is.read(buff, 0, 100)) > 0) {
                swapStream.write(buff, 0, rc);
            }
            data = swapStream.toByteArray();
        } catch (IOException e) {
            e.printStackTrace();
        } finally {
            if (is != null) {
                try {
                    is.close();
                } catch (IOException e) {
                    throw new Exception("输入流关闭异常");
                }
            }
        }

        return Base64.getEncoder().encodeToString(data);
    }

}
