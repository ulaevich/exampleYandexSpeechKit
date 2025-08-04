import json
import time
from typing import Optional
import jwt
from yandex.cloud.iam.v1.iam_token_service_pb2 import CreateIamTokenRequest
from yandex.cloud.iam.v1.iam_token_service_pb2_grpc import IamTokenServiceStub
import yandexcloud


class YandexIAMTokenManager:
    def __init__(self, key_path: Optional[str] = None):
        self.key_path = key_path
        self.private_key = None
        self.key_id = None
        self.service_account_id = None
        self.load_key()

        # Проверяем, что все необходимые поля загружены
        if not all([self.private_key, self.key_id, self.service_account_id]):
            raise ValueError("Failed to load required key information")

    def load_key(self):
        try:
            with open(self.key_path, "r") as f:
                obj = json.load(f)
                self.private_key = obj.get("private_key")
                self.key_id = obj.get("id")
                self.service_account_id = obj.get("service_account_id")

                # Убедимся, что ключ в правильном формате
                if (
                    self.private_key
                    and "-----BEGIN PRIVATE KEY-----" not in self.private_key
                ):
                    self.private_key = f"-----BEGIN PRIVATE KEY-----\n{self.private_key}\n-----END PRIVATE KEY-----"

        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to load key: {str(e)}")

    def create_jwt(self) -> str:
        if not self.private_key:
            raise ValueError("Private key is not loaded")

        now = int(time.time())
        payload = {
            "aud": "https://iam.api.cloud.yandex.net/iam/v1/tokens",
            "iss": self.service_account_id,
            "iat": now,
            "exp": now + 3600,
        }

        try:
            return jwt.encode(
                payload,
                self.private_key,
                algorithm="PS256",
                headers={"kid": self.key_id},
            )
        except Exception as e:
            raise ValueError(f"Failed to create JWT: {str(e)}")

    def create_iam_token(self) -> str:
        try:
            jwt_token = self.create_jwt()
            sdk = yandexcloud.SDK(
                service_account_key={
                    "id": self.key_id,
                    "service_account_id": self.service_account_id,
                    "private_key": self.private_key,
                }
            )
            iam_service = sdk.client(IamTokenServiceStub)
            iam_token = iam_service.Create(CreateIamTokenRequest(jwt=jwt_token))
            return iam_token.iam_token
        except Exception as e:
            raise ValueError(f"Failed to create IAM token: {str(e)}")


token_manager = YandexIAMTokenManager(key_path="authorized_key.json")

token = token_manager.create_iam_token()
