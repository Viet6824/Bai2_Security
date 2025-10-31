# Bài 2 : Chữ ký số
### Tên: Nguyễn Đức Việt
### MSSV K225480106075
Chủ đề: Chữ ký số trong file PDF  
Giảng viên: Đỗ Duy Cốp   
Thời điểm giao: 2025-10-24 11:45  
Đối tượng áp dụng: Toàn bộ sv lớp học phần 58KTPM  
Hạn nộp: Sv upload tất cả lên github trước 2025-10-31 23:59:59  
#### I. MÔ TẢ CHUNG
Sinh viên thực hiện báo cáo và thực hành: phân tích và hiện thực việc nhúng, xác thực chữ ký số trong file PDF.  
Phải nêu rõ chuẩn tham chiếu (PDF 1.7 / PDF 2.0, PAdES/ETSI) và sử dụng công cụ  thực thi (ví dụ iText7, OpenSSL, PyPDF, pdf-lib).
#### II. CÁC YÊU CẦU CỤ THỂ
1) Cấu trúc PDF liên quan chữ ký (Nghiên cứu)
- Mô tả ngắn gọn: Catalog, Pages tree, Page object, Resources, Content streams,
XObject, AcroForm, Signature field (widget), Signature dictionary (/Sig),
/ByteRange, /Contents, incremental updates, và DSS (theo PAdES).
- Liệt kê object refs quan trọng và giải thích vai trò của từng object trong
lưu/truy xuất chữ ký.
- Đầu ra: 1 trang tóm tắt + sơ đồ object (ví dụ: Catalog → Pages → Page → /Contents
; Catalog → /AcroForm → SigField → SigDict).
2) Thời gian ký được lưu ở đâu?
- Nêu tất cả vị trí có thể lưu thông tin thời gian:
 + /M trong Signature dictionary (dạng text, không có giá trị pháp lý).
 + Timestamp token (RFC 3161) trong PKCS#7 (attribute timeStampToken).
 + Document timestamp object (PAdES).
 + DSS (Document Security Store) nếu có lưu timestamp và dữ liệu xác minh.
- Giải thích khác biệt giữa thông tin thời gian /M và timestamp RFC3161.
3) Các bước tạo và lưu chữ ký trong PDF (đã có private RSA)
- Viết script/code thực hiện tuần tự:
 1. Chuẩn bị file PDF gốc.
 2. Tạo Signature field (AcroForm), reserve vùng /Contents (8192 bytes).
 3. Xác định /ByteRange (loại trừ vùng /Contents khỏi hash).
 4. Tính hash (SHA-256/512) trên vùng ByteRange.
 5. Tạo PKCS#7/CMS detached hoặc CAdES:
 - Include messageDigest, signingTime, contentType.
 - Include certificate chain.
 - (Tùy chọn) thêm RFC3161 timestamp token.
 6. Chèn blob DER PKCS#7 vào /Contents (hex/binary) đúng offset.
 7. Ghi incremental update.
 8. (LTV) Cập nhật DSS với Certs, OCSPs, CRLs, VRI.
- Phải nêu rõ: hash alg, RSA padding, key size, vị trí lưu trong PKCS#7.
- Đầu ra: mã nguồn, file PDF gốc, file PDF đã ký.
4) Các bước xác thực chữ ký trên PDF đã ký
- Các bước kiểm tra:
 1. Đọc Signature dictionary: /Contents, /ByteRange.
 2. Tách PKCS#7, kiểm tra định dạng.
 3. Tính hash và so sánh messageDigest.
 4. Verify signature bằng public key trong cert.
 5. Kiểm tra chain → root trusted CA.
 6. Kiểm tra OCSP/CRL.
 7. Kiểm tra timestamp token.
 8. Kiểm tra incremental update (phát hiện sửa đổi).
- Nộp kèm script verify + log kiểm thử.
---
#### III. YÊU CẦU NỘP BÀI
1. Báo cáo PDF ≤ 6 trang: mô tả cấu trúc, thời gian ký, rủi ro bảo mật.
2. Code + README (Git repo hoặc zip).
3. Demo files: original.pdf, signed.pdf, tampered.pdf.
4. (Tuỳ chọn) Video 3–5 phút demo kết quả.
---
#### IV. TIÊU CHÍ CHẤM
- Lý thuyết & cấu trúc PDF/chữ ký: 25%
- Quy trình tạo chữ ký đúng kỹ thuật: 30%
- Xác thực đầy đủ (chain, OCSP, timestamp): 25%
- Code & demo rõ ràng: 15%
- Sáng tạo mở rộng (LTV, PAdES): 5%
---
#### V. GHI CHÚ AN TOÀN
- Vẫn lưu private key (sinh random) trong repo. Tránh dùng private key thương mại.
- Dùng RSA ≥ 2048-bit và SHA-256 hoặc mạnh hơn.
- Có thể dùng RSA-PSS thay cho PKCS#1 v1.5.
- Khuyến khích giải thích rủi ro: padding oracle, replay, key leak.
---
#### VI. GỢI Ý CÔNG CỤ
- OpenSSL, iText7/BouncyCastle, pypdf/PyPDF2.
- Tham khảo chuẩn PDF: ISO 32000-2 (PDF 2.0) và ETSI EN 319 142 (PAdES).
## Bài làm
#### 1. Cấu Trúc PDF Liên Quan Chữ Ký (Nghiên Cứu)
PDF là định dạng dựa trên object, với cấu trúc cây. Các object chính liên quan đến chữ ký số bao gồm:  
Catalog (/Root): Object gốc của PDF, chứa tham chiếu đến Pages tree và AcroForm. Vai trò: Làm trung tâm lưu trữ metadata, bao gồm /AcroForm cho form fields như signature.  
Pages tree: Cấu trúc cây các trang (/Pages), chứa Page objects. Vai trò: Tổ chức nội dung trang, nhưng chữ ký thường không ảnh hưởng trực tiếp trừ khi visible signature (widget annotation trên Page).  
Page object: Đại diện một trang, chứa /Resources, /Contents. Vai trò: Nếu signature visible, Signature field (widget) được thêm vào /Annots của Page.  
Resources: Dictionary chứa font, XObject (images/forms). Vai trò: Hỗ trợ render widget signature nếu có appearance stream.  
Content streams: Dữ liệu hiển thị trang (operators như text, path). Vai trò: Không trực tiếp liên quan chữ ký, nhưng hash bao gồm chúng.  
XObject: Object bên ngoài (Form XObject cho appearance). Vai trò: Sử dụng cho appearance của signature widget.  
AcroForm: Dictionary trong Catalog, chứa /Fields (mảng fields). Vai trò: Quản lý form fields, bao gồm Signature field.  
Signature field (widget): Một field trong /Fields, là annotation trên Page. Vai trò: Đại diện vị trí visible signature, chứa tham chiếu đến Signature dictionary.  
Signature dictionary (/Sig): Dictionary trong Signature field, chứa /Filter (e.g., Adobe.PPKLite), /SubFilter (adbe.pkcs7.detached), /ByteRange, /Contents. Vai trò: Lưu metadata chữ ký.  
/ByteRange: Mảng chỉ vùng bytes được hash (loại trừ /Contents). Vai trò: Xác định phạm vi tính hash.  
/Contents: Hex string chứa PKCS#7/CMS blob (DER encoded). Vai trò: Lưu chữ ký thực tế.  
Incremental updates: Cập nhật PDF bằng cách append bytes mới mà không overwrite. Vai trò: Cho phép thêm chữ ký mà giữ nguyên nội dung cũ, dễ kiểm tra tamper.  
DSS (Document Security Store): Dictionary trong Catalog (/DSS), chứa /Certs, /OCSPs, /CRLs, /VRI. Vai trò: Lưu dữ liệu xác minh LTV (Long-Term Validation) để xác thực offline.  
Object refs quan trọng và vai trò:  
Catalog (ref 1 0): Lưu AcroForm và DSS.  
AcroForm (ref e.g., 10 0): Lưu SigField.  
SigField (ref e.g., 11 0): Lưu SigDict.  
SigDict (ref e.g., 12 0): Lưu /ByteRange, /Contents.  
DSS (ref e.g., 20 0): Lưu certs cho LTV.  
Sơ đồ object (text-based):  
textCatalog → /AcroForm → SigField (widget) → SigDict (/Sig) → /ByteRange, /Contents  
Catalog → Pages → Page → /Annots → Widget (if visible)  
Catalog → /DSS → /Certs, /OCSPs, /CRLs, /VRI (per signature)  
#### 2. Thời Gian Ký Được Lưu Ở Đâu?
Thông tin thời gian ký có thể lưu ở nhiều vị trí, nhưng độ tin cậy khác nhau:  
/M trong Signature dictionary: Lưu dạng text (e.g., D:20251031000000+07'00'). Vai trò: Thời gian báo cáo bởi signer, không có giá trị pháp lý vì có thể giả mạo.  
Timestamp token (RFC 3161) trong PKCS#7: Lưu trong attribute timeStampToken (unsigned attrs của SignerInfo). Vai trò: Thời gian trusted từ TSA (Time Stamping Authority), chống backdating.  
Document timestamp object (PAdES): Một signature đặc biệt chỉ chứa timestamp, không cert. Vai trò: Bảo vệ toàn bộ document, bao gồm signatures trước, cho LTV.  
DSS: Lưu timestamp và dữ liệu xác minh (OCSP responses chứa thời gian). Vai trò: Hỗ trợ xác thực dài hạn.  
Khác biệt giữa /M và timestamp RFC3161: /M là self-reported, không trusted, có thể chỉnh sửa. Timestamp RFC3161 là signed bởi TSA trusted, có giá trị pháp lý, chứng minh thời gian tại lúc ký.
#### Rủi Ro Bảo Mật
Padding oracle: Tấn công trên PKCS#1 v1.5, khai thác error messages để decrypt. Giải pháp: Sử dụng RSA-PSS.  
Replay: Chữ ký cũ được reuse nếu không có nonce/timestamp unique. Giải pháp: Include signingTime và timestamp.  
Key leak: Private key lộ dẫn đến forgery. Giải pháp: Lưu key an toàn, dùng HSM.  
