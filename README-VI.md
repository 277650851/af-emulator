# Assault Fire Server Emulator

**Ngôn ngữ:** [English](README.md) | [Tagalog](README-TL.md) | [Cebuano](README-CEB.md) | [简体中文](README-ZH-CN.md) | [Ngôn ngữ khác](README-LANGUAGES.md)

Dự án phi chính thức nhằm bảo tồn **Assault Fire PH** và mô phỏng máy chủ của trò chơi. Dự án này và các máy chủ do bên thứ ba vận hành không liên kết, được tài trợ hay được Tencent, Level Up! Games hoặc chủ sở hữu quyền ban đầu xác nhận. Máy chủ cộng đồng hoạt động độc lập.

> **Chỉ hỗ trợ và kiểm thử:** Assault Fire PH **v1.0.0.24**. Kho mã này không chứa tệp trò chơi. Bạn phải tự có các tệp game của mình.

## Cách bắt đầu đơn giản nhất

1. Đặt toàn bộ thư mục `af-emulator` bên trong thư mục game Assault Fire PH.
2. Nhấp chuột phải vào `START_ASSAULT_FIRE.ps1`, chọn **Run with PowerShell**. Cho phép quyền Administrator nếu Windows hỏi.
3. Trình khởi chạy kiểm tra phiên bản và cấu hình, chuẩn bị khóa cục bộ, rồi khởi động máy chủ, công cụ hỗ trợ chạy game và client.
4. Đăng nhập trong client. Khi nút **START** xuất hiện, hãy nhấp để tiếp tục.

Với quy trình một lần bấm thông thường, bạn không cần tự chạy máy chủ hoặc công cụ vá. Script không tải xuống hay phân phối tệp game; nó chỉ dùng các tệp cục bộ của bạn. Nếu phiên bản không khớp hoặc không xác minh được chữ ký của `TGame.exe` hay `TCLS.dll`, hãy dừng lại và không ép áp dụng bản vá. Trước khi chạy game, trình khởi chạy áp dụng vĩnh viễn bản vá ngày giờ đã xác minh cho `TGame.exe` sau khi tạo bản sao lưu giống hệt từng byte tên `TGame.exe.bak`. Nếu không có vùng mã an toàn, trình khởi chạy thêm một section PE thực thi nhỏ `.afdt` chỉ khi header còn slot section trống; nếu không, tệp sẽ không bị sửa đổi.

## Thiết lập thủ công và dành cho nhà phát triển

Xem [hướng dẫn đầy đủ bằng tiếng Anh](README.md) để biết tất cả bước và lệnh chính xác. Bạn cần Windows, Python 3.10 trở lên và bản game được hỗ trợ của riêng mình. Khi thiết lập thủ công, hãy đợi preflight hiển thị `UNLOCKED`. Nếu tự khởi chạy game, đừng nhấn **START** trước khi công cụ hỗ trợ hiển thị `TCLS ARMED`. Tùy chọn `--server-only` chỉ dành cho việc host máy chủ; nó không mở khóa chạy game cục bộ.

## Trạng thái và hỗ trợ

Bản ổn định công khai hiện tại là **v143b**. Các luồng VERSION, AUTH, DIR, ROLE, ZONE, quản lý phòng và trận PvE đang hoạt động. Tạo nickname/tài khoản lần đầu và một số tính năng xã hội/tiến trình vẫn đang phát triển. Đồng bộ AP ban đầu ở client hiện dùng giải pháp cục bộ tạm thời.

Khi cần trợ giúp, hãy gửi ảnh lỗi, bước bạn đang thực hiện, lệnh chính xác đã chạy, `server/af_server_live.log` và phiên bản game. **Không gửi** `PRIVATE.PEM`, mật khẩu, thông tin đăng nhập, token hoặc tệp game gốc.

- [Trạng thái dự án](docs/STATUS.md) · [Lỗi trình khởi chạy](docs/LAUNCHER_ERRORS.md) · [Ghi chú thiết lập quan trọng](docs/VITAL_SETUP_NOTES.md) · [Mục lục tài liệu](docs/README.md)
- [Tất cả README theo ngôn ngữ](README-LANGUAGES.md)

**Giấy phép:** MIT.
