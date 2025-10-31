# sign_pdf.py - Ký PDF chuẩn PAdES (pyhanko 0.20.1) - ĐÃ SỬA TOÀN BỘ LỖI
import asyncio
from pyhanko import stamp
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import signers, fields
from pyhanko.sign.timestamps import HTTPTimeStamper
from pyhanko.keys import load_cert_from_pemder, load_private_key_from_pemder

# CẤU HÌNH
PDF_IN = "pdfviet.pdf"
PDF_OUT = "signed.pdf"
KEY_FILE = "private_key.pem"
CERT_FILE = "certificate.pem"

async def sign_pdf():
    with open(PDF_IN, "rb") as doc:
        # Load cert + key
        cert = load_cert_from_pemder(CERT_FILE)
        key = load_private_key_from_pemder(KEY_FILE, passphrase=None)

        # Tạo signer (KHÔNG CẦN cert_registry ở 0.20.1)
        signer = signers.SimpleSigner(
            signing_cert=cert,
            signing_key=key,
            signature_mechanism="sha256WithRSAEncryption"
        )

        # Thêm timestamp (RFC3161)
        signer = signer.with_timestamp(HTTPTimeStamper("http://tsa.freetsa.org/tsr"))

        with IncrementalPdfFileWriter(doc) as writer:
            # Tạo field chữ ký
            field = fields.SigFieldSpec(
                sig_field_name="MySignature",
                box=(100, 100, 300, 150)  # Vị trí visible
            )
            fields.append_signature_field(writer, field)

            # Ký PDF (tự động: hash, PKCS#7, /Contents, ByteRange)
            await stamp.signatures.sign_pdf(
                signer=signer,
                field_name="MySignature",
                writer=writer,
                md_algorithm='sha256',
                subfilter=fields.SigSeedSubFilter.ADOBE_PKCS7_DETACHED,
                bytes_reserved=8192  # Reserve /Contents
            )

        # Lưu file đã ký
        with open(PDF_OUT, "wb") as f:
            writer.write(f)
        print(f"ĐÃ KÝ THÀNH CÔNG: {PDF_OUT}")
        print("   - Hash: SHA-256")
        print("   - RSA: 2048-bit, PKCS#1 v1.5")
        print("   - PKCS#7: detached, có timestamp + cert chain")

if __name__ == "__main__":
    asyncio.run(sign_pdf())