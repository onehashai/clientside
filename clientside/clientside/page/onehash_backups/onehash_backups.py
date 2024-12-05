import requests
import frappe
import os
import boto3
import datetime

@frappe.whitelist()
def get_context(context):
    def get_download_link(key):
        from botocore.client import Config
        from botocore.exceptions import ClientError

        bucket_name = frappe.conf.aws_bucket_name
        try:
            conn = boto3.client(
                "s3",
                aws_access_key_id=frappe.conf.aws_access_key_id,
                aws_secret_access_key=frappe.conf.aws_secret_access_key,
                config=Config(signature_version="s3v4", region_name="ap-south-1"),
            )
            url = conn.generate_presigned_url(
                "get_object", Params={"Bucket": bucket_name, "Key": key}, ExpiresIn=300
            )
            return url
        except ClientError as e:
            print(f"Error generating pre-signed URL: {e}")
            return None

    def get_time(created_on):
        created_on_datetime = datetime.datetime.strptime(created_on, "%Y-%m-%d %H:%M:%S.%f")
        return created_on_datetime.strftime("%a %b %d %H:%M %Y")

    req = requests.get(
        "http://"
        + frappe.conf.admin_url
        + "/api/method/bettersaas.bettersaas.doctype.saas_sites_backup.saas_sites_backup.get_backups?site="
        + frappe.local.site
    ).json()

    files = req["message"]
    filtered_files = [
        (
            get_download_link(file["path"]), 
            get_time(file["created_on"]),
            file["encrypted"],
            file["size"]
        )
        for file in files
    ]
    return {"files": filtered_files}