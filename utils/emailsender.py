import boto3
from botocore.exceptions import ClientError
import config
import traceback


def send_email_ses(to, subject, html_body, text_body=None):
    """
    Send email via AWS SES.
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject
        html_body (str): Email HTML content
        text_body (str, optional): Plain text content (auto-generated if not provided)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not text_body:
        text_body = "This email contains HTML content. Please view it in an HTML-capable client."

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
