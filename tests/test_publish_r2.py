import sys
import types

from sa_gbv_data import publish_r2


def test_upload_tree_replaces_stable_latest_keys(monkeypatch, tmp_path):
    (tmp_path / "processed").mkdir()
    (tmp_path / "processed" / "layer.pmtiles").write_bytes(b"tiles")
    (tmp_path / "processed" / "layer.parquet").write_bytes(b"parquet")
    uploads = []

    class FakeClient:
        def upload_file(self, filename, bucket, key, ExtraArgs):
            uploads.append((filename, bucket, key, ExtraArgs))

    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.client = lambda service, **kwargs: FakeClient()
    fake_botocore_config = types.ModuleType("botocore.config")
    fake_botocore_config.Config = lambda **kwargs: kwargs
    fake_botocore = types.ModuleType("botocore")
    fake_botocore.config = fake_botocore_config
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setitem(sys.modules, "botocore", fake_botocore)
    monkeypatch.setitem(sys.modules, "botocore.config", fake_botocore_config)

    assert publish_r2.upload_tree(
        tmp_path,
        bucket="public-data",
        endpoint_url="https://r2.example",
    ) == 2
    assert [upload[2] for upload in uploads] == [
        "latest/processed/layer.parquet",
        "latest/processed/layer.pmtiles",
    ]
    assert uploads[0][3]["ContentType"] == "application/vnd.apache.parquet"
    assert uploads[1][3]["ContentType"] == "application/vnd.pmtiles"


def test_upload_tree_skips_repository_placeholders(monkeypatch, tmp_path):
    (tmp_path / ".gitkeep").write_bytes(b"")
    (tmp_path / "layer.parquet").write_bytes(b"parquet")
    uploads = []

    class FakeClient:
        def upload_file(self, filename, bucket, key, ExtraArgs):
            uploads.append(key)

    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.client = lambda service, **kwargs: FakeClient()
    fake_botocore_config = types.ModuleType("botocore.config")
    fake_botocore_config.Config = lambda **kwargs: kwargs
    fake_botocore = types.ModuleType("botocore")
    fake_botocore.config = fake_botocore_config
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setitem(sys.modules, "botocore", fake_botocore)
    monkeypatch.setitem(sys.modules, "botocore.config", fake_botocore_config)

    publish_r2.upload_tree(tmp_path, bucket="bucket", endpoint_url="https://r2.example")
    assert uploads == ["latest/layer.parquet"]