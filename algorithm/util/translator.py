import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tmt.v20180321 import tmt_client, models
from config import DevConfig

class TencentTranslator:
    def __init__(self, secret_id=None, secret_key=None):
        self.secret_id = secret_id or DevConfig.TENCENT_SECRET_ID
        self.secret_key = secret_key or DevConfig.TENCENT_SECRET_KEY
        self.client = None

        if self.secret_id and self.secret_key:
            try:
                cred = credential.Credential(self.secret_id, self.secret_key)
                httpProfile = HttpProfile()
                httpProfile.endpoint = "tmt.tencentcloudapi.com"

                clientProfile = ClientProfile()
                clientProfile.httpProfile = httpProfile
                # Region does not matter much for TMT, ap-guangzhou is fine
                self.client = tmt_client.TmtClient(cred, "ap-guangzhou", clientProfile)
            except Exception as e:
                print(f"[Translator] 初始化失败: {e}")

    def translate_zh_to_en(self, text):
        if not self.client:
            print("[Translator] 未配置腾讯云密钥，无法翻译，将返回原文本。")
            return text
            
        if not text or not text.strip():
            return text

        try:
            req = models.TextTranslateRequest()
            req.SourceText = text
            req.Source = "zh"
            req.Target = "en"
            req.ProjectId = 0

            resp = self.client.TextTranslate(req)
            result = resp.TargetText
            print(f"[Translator] 翻译成功: '{text}' -> '{result}'")
            return result
        except TencentCloudSDKException as err:
            print(f"[Translator] 翻译请求出错: {err}")
            return text

# 测试代码
if __name__ == "__main__":
    translator = TencentTranslator()
    res = translator.translate_zh_to_en("红色的车, 拿着雨伞的人")
    print("Test Result:", res)
