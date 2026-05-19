CREATE DATABASE QL_DOIBONGDA
USE QL_DOIBONGDA
CREATE TABLE CauLacBo (
    MaCLB          VARCHAR(10)   PRIMARY KEY,
    TenCLB         NVARCHAR(100) NOT NULL,
    TenDayDu       NVARCHAR(150),
    NgayThanhLap   DATE,
    SanNha         NVARCHAR(100),
    Logo           VARCHAR(255),          
    MaHLVTruong    VARCHAR(10)   NULL,    
    Website        VARCHAR(150),
    Email          VARCHAR(100),
    SoDienThoai    VARCHAR(15),
    DiaChi         NVARCHAR(200)
);



CREATE TABLE HuanLuyenVien (
    MaHLV          VARCHAR(10)   PRIMARY KEY,
    HoTen          NVARCHAR(100) NOT NULL,
    NgaySinh       DATE,
    QuocTich       NVARCHAR(50),
    LoaiHLV        NVARCHAR(50),          
    NgayBatDau     DATE,
    NgayKetThuc    DATE           NULL,
    Luong          DECIMAL(15,2)  NULL,
    SoDienThoai    VARCHAR(15),
    Email          VARCHAR(100),
    MaCLB          VARCHAR(10)    NULL      
);

CREATE TABLE CauThu (
    MaCauThu       VARCHAR(10)   PRIMARY KEY,
    HoTen          NVARCHAR(100) NOT NULL,
    NgaySinh       DATE          NOT NULL,
    QuocTich       NVARCHAR(50),
    ChieuCao       DECIMAL(5,2),           
    CanNang        DECIMAL(6,2),            
    SoAo           INT           NULL,
    ViTriChinh     NVARCHAR(50),            
    MaCLB          VARCHAR(10)   NULL,      
    NgayGiaNhap    DATE,
    NgayHetHanHopDong DATE        NULL,
    GiaTriThiTruong DECIMAL(15,2) NULL,    
    TrangThai      NVARCHAR(50)  DEFAULT N'Còn thi đấu'  
);



CREATE TABLE ViTri (
    MaViTri        VARCHAR(10)   PRIMARY KEY,
    TenViTri       NVARCHAR(50)  NOT NULL,  
    MoTa           NVARCHAR(200)
);

CREATE TABLE CauThu_ViTri (
    MaCauThu       VARCHAR(10)   NOT NULL,
    MaViTri        VARCHAR(10)   NOT NULL,
    PRIMARY KEY (MaCauThu, MaViTri)
);

CREATE TABLE TranDau (
    MaTran         INT           IDENTITY(1,1) PRIMARY KEY,
    NgayThiDau     DATETIME      NOT NULL,
    VongDau        INT,
    GiaiDau        NVARCHAR(100),          
    SanVanDong     NVARCHAR(100),
    DoiNha         VARCHAR(10)   NOT NULL,
    DoiKhach       VARCHAR(10)   NOT NULL,
    TySo           VARCHAR(20),            
    KetQua         NVARCHAR(20),           
    GhiChu         NVARCHAR(500)
);

CREATE TABLE ThongKeCauThu_TranDau (
    MaThongKe      INT           IDENTITY(1,1) PRIMARY KEY,
    MaTran         INT           NOT NULL,
    MaCauThu       VARCHAR(10)   NOT NULL,
    SoPhutThiDau   INT           DEFAULT 0,
    SoBanThang     INT           DEFAULT 0,
    SoKienTao      INT           DEFAULT 0,
    TheVang        INT           DEFAULT 0,
    TheDo          INT           DEFAULT 0,
    SoPhaCuuThua   INT           DEFAULT 0,  
    DanhGia        DECIMAL(3,1)  NULL,         
    GhiChu         NVARCHAR(200)
);

CREATE TABLE HopDong (
    MaHopDong      INT           IDENTITY(1,1) PRIMARY KEY,
    MaCauThu       VARCHAR(10)   NOT NULL,
    MaCLB          VARCHAR(10)   NOT NULL,
    NgayKy         DATE,
    NgayBatDau     DATE,
    NgayKetThuc    DATE,
    GiaTriHopDong  DECIMAL(18,2),
    LuongThang     DECIMAL(15,2),
    DieuKhoanBonus NVARCHAR(500),
    TrangThai      NVARCHAR(50)  DEFAULT N'Hiệu lực'
);
ALTER TABLE CauLacBo
    ADD CONSTRAINT FK_CauLacBo_HLV
    FOREIGN KEY (MaHLVTruong) REFERENCES HuanLuyenVien(MaHLV);

ALTER TABLE HuanLuyenVien
    ADD CONSTRAINT FK_HLV_CauLacBo
    FOREIGN KEY (MaCLB) REFERENCES CauLacBo(MaCLB);

ALTER TABLE CauThu
    ADD CONSTRAINT FK_CauThu_CauLacBo
    FOREIGN KEY (MaCLB) REFERENCES CauLacBo(MaCLB);

ALTER TABLE ThongKeCauThu_TranDau
    ADD CONSTRAINT FK_ThongKe_TranDau
    FOREIGN KEY (MaTran) REFERENCES TranDau(MaTran);

ALTER TABLE ThongKeCauThu_TranDau
    ADD CONSTRAINT FK_ThongKe_CauThu
    FOREIGN KEY (MaCauThu) REFERENCES CauThu(MaCauThu);

ALTER TABLE TranDau
    ADD CONSTRAINT FK_TranDau_DoiNha
    FOREIGN KEY (DoiNha) REFERENCES CauLacBo(MaCLB);

ALTER TABLE TranDau
    ADD CONSTRAINT FK_TranDau_DoiKhach
    FOREIGN KEY (DoiKhach) REFERENCES CauLacBo(MaCLB);
INSERT INTO CauLacBo (MaCLB, TenCLB, TenDayDu, NgayThanhLap, SanNha, Logo, MaHLVTruong, Website)
VALUES 
('HCM', N'TP.HCM', N'Câu lạc bộ Bóng đá Thành phố Hồ Chí Minh', '2017-01-01', N'Sân Thống Nhất', 'hcmfc.png', NULL, 'https://hcmfc.vn'),
('HAGL', N'HAGL', N'Hoàng Anh Gia Lai', '2002-01-01', N'Sân Pleiku', 'haglf.png', NULL, 'https://haglf.vn'),
('HNFC', N'Hà Nội FC', N'Câu lạc bộ Bóng đá Hà Nội', '2006-01-01', N'Sân Hàng Đẫy', 'hnfc.png', NULL, 'https://hnfc.vn'),
('Viettel', N'Viettel FC', N'Câu lạc bộ Bóng đá Viettel', '1980-01-01', N'Sân Mỹ Đình', 'viettelfc.png', NULL, NULL),
('Bình Dương', N'Becamex Bình Dương', N'Câu lạc bộ Bóng đá Becamex Bình Dương', '1976-01-01', N'Sân Gò Đậu', 'binhduongfc.png', NULL, NULL);
INSERT INTO HuanLuyenVien (MaHLV, HoTen, NgaySinh, QuocTich, LoaiHLV, NgayBatDau, Luong, MaCLB)
VALUES 
('HLV001', N'Vũ Tiến Thành', '1981-05-12', N'Việt Nam', N'HLV trưởng', '2024-06-01', 120000000, 'HCM'),
('HLV002', N'Kiatisuk Senamuang', '1973-08-11', N'Thái Lan', N'HLV trưởng', '2022-11-01', 180000000, 'HAGL'),
('HLV003', N'Bandovic', '1973-08-11', N'Montenegro', N'HLV trưởng', '2024-05-15', 200000000, 'HNFC'),
('HLV004', N'Bae Ji-won', '1982-03-25', N'Hàn Quốc', N'HLV trưởng', '2025-01-10', 150000000, 'Viettel'),
('HLV005', N'Lê Huỳnh Đức', '1972-04-20', N'Việt Nam', N'HLV trưởng', '2023-10-01', 110000000, 'Bình Dương');
INSERT INTO CauThu (MaCauThu, HoTen, NgaySinh, QuocTich, ChieuCao, CanNang, SoAo, ViTriChinh, MaCLB, NgayGiaNhap, GiaTriThiTruong, TrangThai)
VALUES 
('CT001', N'Nguyễn Văn Toàn', '1996-04-12', N'Việt Nam', 170, 65, 11, N'Tiền đạo cánh', 'HAGL', '2023-01-05', 350000000, N'Còn thi đấu'),
('CT002', N'Nguyễn Quang Hải', '1997-04-12', N'Việt Nam', 168, 65, 19, N'Tiền vệ tấn công', 'HCM', '2025-02-01', 800000000, N'Còn thi đấu'),
('CT003', N'Đỗ Hùng Dũng', '1993-09-08', N'Việt Nam', 178, 72, 8, N'Tiền vệ trung tâm', 'HNFC', '2024-01-01', 1200000000, N'Còn thi đấu'),
('CT004', N'Nguyễn Hoàng Đức', '1998-01-11', N'Việt Nam', 183, 75, 28, N'Tiền vệ trung tâm', 'Viettel', '2020-01-01', 1500000000, N'Còn thi đấu'),
('CT005', N'Phạm Tuấn Hải', '1998-09-12', N'Việt Nam', 172, 68, 10, N'Tiền đạo', 'HAGL', '2022-06-15', 600000000, N'Còn thi đấu'),
('CT006', N'Nguyễn Filip', '1992-03-14', N'Cộng hòa Séc', 192, 88, 1, N'Thủ môn', 'HNFC', '2023-07-20', 900000000, N'Còn thi đấu');
INSERT INTO ViTri (MaViTri, TenViTri, MoTa)
VALUES 
('GK', N'Thủ môn', N'Người giữ gôn'),
('CB', N'Trung vệ', N'Hậu vệ trung tâm'),
('LB', N'Hậu vệ trái', N'Hậu vệ biên trái'),
('RB', N'Hậu vệ phải', N'Hậu vệ biên phải'),
('DM', N'Tiền vệ phòng ngự', N'Tiền vệ trụ'),
('CM', N'Tiền vệ trung tâm', N'Tiền vệ trung tâm'),
('AM', N'Tiền vệ tấn công', N'Tiền vệ tổ chức'),
('LW', N'Cánh trái', N'Tiền đạo cánh trái'),
('RW', N'Cánh phải', N'Tiền đạo cánh phải'),
('ST', N'Tiền đạo cắm', N'Tiền đạo trung tâm');
INSERT INTO CauThu_ViTri (MaCauThu, MaViTri)
VALUES 
('CT001', 'LW'), ('CT001', 'RW'),
('CT002', 'AM'), ('CT002', 'CM'), ('CT002', 'RW'),
('CT003', 'CM'), ('CT003', 'DM'),
('CT004', 'CM'), ('CT004', 'AM'),
('CT005', 'ST'), ('CT005', 'AM'),
('CT006', 'GK');
INSERT INTO TranDau (NgayThiDau, VongDau, GiaiDau, SanVanDong, DoiNha, DoiKhach, TySo, KetQua)
VALUES 
('2025-02-15 19:00:00', 1, N'V.League 2025', N'Sân Pleiku', 'HAGL', 'HCM', '2-1', N'Thắng'),
('2025-02-22 17:00:00', 2, N'V.League 2025', N'Sân Thống Nhất', 'HCM', 'HNFC', '1-1', N'Hòa'),
('2025-03-01 19:15:00', 3, N'V.League 2025', N'Sân Mỹ Đình', 'Viettel', 'HAGL', '0-2', N'Thua'),
('2025-03-08 19:00:00', 4, N'V.League 2025', N'Sân Gò Đậu', 'Bình Dương', 'HNFC', '3-2', N'Thắng'),
('2025-03-15 17:00:00', 5, N'V.League 2025', N'Sân Hàng Đẫy', 'HNFC', 'Viettel', NULL, NULL);
INSERT INTO ThongKeCauThu_TranDau (MaTran, MaCauThu, SoPhutThiDau, SoBanThang, SoKienTao, TheVang, TheDo, DanhGia)
VALUES 
(1, 'CT001', 90, 1, 0, 0, 0, 8.2),     
(1, 'CT005', 82, 1, 1, 0, 0, 8.7),     
(2, 'CT002', 90, 1, 0, 1, 0, 7.5),     
(3, 'CT001', 90, 1, 0, 0, 0, 7.9),
(3, 'CT005', 90, 1, 0, 0, 0, 8.1),
(4, 'CT006', 90, 0, 0, 0, 0, 6.8);    