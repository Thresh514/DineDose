import boto3
from botocore.exceptions import ClientError
import config
import traceback


def send_email_ses(to, subject, html_body, text_body=None):
    """
    通过 AWS SES 发送邮件。
    
    Args:
        to (str): 收件人邮箱
        subject (str): 邮件标题
        html_body (str): 邮件 HTML 内容
        text_body (str, optional): 邮件纯文本内容（默认自动生成）
    
    Returns:
        bool: True 表示发送成功，False 表示失败
    """
    if not text_body:
        text_body = "This email contains HTML content. Please view it in an HTML-capable client."

    # 初始化 SES 客户端
    ses = boto3.client(
        "ses",
        region_name=config.AWS_REGION,
        aws_access_key_id=config.AWS_ACCESS_KEY,
        aws_secret_access_key=config.AWS_SECRET_KEY,
    )

    try:
        response = ses.send_email(
            Source=config.SES_SENDER,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Text": {"Data": text_body},
                    "Html": {"Data": html_body},
                },
            },
        )
        print(f"✅ [SES] Sent email to {to}, MessageId={response['MessageId']}")
        return True

    except ClientError as e:
        print(f"❌ [SES Error] {e.response['Error']['Message']}")
        traceback.print_exc()
        return False

    except Exception as e:
        print(f"❌ [Unknown Error] {e}")
        traceback.print_exc()
        return False
