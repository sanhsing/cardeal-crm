"""
車行寶 CRM v5.3 - 完整展示種子資料
模擬 2025/01/01 ~ 2026/02/03 營運資料
人員：老闆1 + 經理2 + 業務3
北斗七星文創數位 × 織明
"""
import os
import sqlite3
import hashlib
import random
from datetime import datetime, timedelta

random.seed(42)  # 固定隨機種子，每次部署資料一致


def seed_demo_data(db_path):
    """載入完整展示資料"""
    if not os.path.exists(db_path):
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 檢查是否已有展示資料
    c.execute("SELECT COUNT(*) FROM customers")
    if c.fetchone()[0] > 0:
        conn.close()
        return

    # ================================================================
    # 1. 人員（老闆1 + 經理2 + 業務3）
    # ================================================================
    pwd = hashlib.sha256('demo1234'.encode()).hexdigest()

    # user_id=1 已存在（演示帳號），更新為老闆
    c.execute("""UPDATE users SET name='陳永發', role='admin',
                 permissions='["all"]' WHERE id=1""")

    staff = [
        ('林志明', '0923001001', pwd, 'manager', '["view_all","edit_all","report"]'),
        ('張美華', '0923001002', pwd, 'manager', '["view_all","edit_all","report"]'),
        ('王建志', '0923001003', pwd, 'staff',   '["view_own","edit_own"]'),
        ('李佳蓉', '0923001004', pwd, 'staff',   '["view_own","edit_own"]'),
        ('黃志豪', '0923001005', pwd, 'staff',   '["view_own","edit_own"]'),
    ]
    for s in staff:
        try:
            c.execute("""INSERT INTO users (name, phone, password, role, permissions,
                         created_at, status) VALUES (?,?,?,?,?,'2025-01-01','active')""", s)
        except:
            pass

    # user_id: 1=陳永發(老闆) 2=林志明(經理) 3=張美華(經理)
    #          4=王建志(業務) 5=李佳蓉(業務) 6=黃志豪(業務)
    sales_ids = [4, 5, 6]
    all_staff_ids = [1, 2, 3, 4, 5, 6]
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 2, 3)
    total_days = (end_date - start_date).days

    # ================================================================
    # 2. 客戶資料（50 筆，分散 14 個月）
    # ================================================================
    customer_data = [
        ('王大明', '0911001001', 'wang.dm@mail.com', '台北市信義區松仁路100號', 'M', '1985-03-15', 'referral', 'vip', '["換車","預算高"]', '老客戶，回購率高'),
        ('李美玲', '0911001002', 'lee.ml@mail.com', '新北市板橋區文化路200號', 'F', '1990-07-22', 'line', 'vip', '["休旅車"]', '偏好 SUV'),
        ('張志強', '0911001003', None, '桃園市中壢區中華路50號', 'M', '1978-11-03', 'walk_in', 'normal', '["商用"]', '運輸業老闆'),
        ('陳雅婷', '0911001004', 'chen.yt@mail.com', '台中市西屯區台灣大道300號', 'F', '1995-01-18', 'facebook', 'normal', '["小車","省油"]', '通勤代步'),
        ('林建宏', '0911001005', None, '高雄市左營區博愛路150號', 'M', '1982-09-28', 'phone', 'vip', '["雙B"]', 'BMW 忠實客戶'),
        ('黃淑芬', '0911001006', 'huang.sf@mail.com', '台南市東區東門路80號', 'F', '1988-04-12', 'web', 'normal', '["家用"]', '安全優先'),
        ('劉俊傑', '0911001007', None, '新竹市東區光復路500號', 'M', '1975-12-30', 'referral', 'vip', '["跑車","性能"]', '車輛收藏家'),
        ('許雅琪', '0911001008', 'hsu.yc@mail.com', '嘉義市西區中山路60號', 'F', '1993-06-05', 'line', 'normal', '["代步"]', '首購族'),
        ('吳明哲', '0911001009', None, '彰化市中正路120號', 'M', '1980-08-20', 'walk_in', 'cold', '[]', '看過未買'),
        ('蔡佳穎', '0911001010', 'tsai.jy@mail.com', '宜蘭市中山路90號', 'F', '1998-02-14', 'facebook', 'normal', '["二手","便宜"]', '預算30萬'),
        ('鄭文彬', '0911001011', None, '基隆市中正區信二路40號', 'M', '1970-05-08', 'phone', 'normal', '["貨車"]', '需要 3.5 噸'),
        ('周怡君', '0911001012', 'chou.yc@mail.com', '花蓮市中山路350號', 'F', '1992-10-25', 'web', 'potential', '["跨界"]', 'CUV 有興趣'),
        ('趙國華', '0911001013', None, '屏東市民生路100號', 'M', '1968-01-30', 'referral', 'vip', '["大車"]', '公司用車採購'),
        ('孫麗華', '0911001014', 'sun.lh@mail.com', '苗栗市中正路200號', 'F', '1985-08-08', 'line', 'normal', '["MPV"]', '三寶媽需要七人座'),
        ('楊家豪', '0911001015', None, '雲林縣斗六市太平路60號', 'M', '1988-03-22', 'walk_in', 'normal', '["性能"]', '改裝愛好者'),
        ('何佳芬', '0911001016', 'ho.cf@mail.com', '台北市大安區忠孝東路400號', 'F', '1991-12-01', 'facebook', 'potential', '["電動車"]', '考慮 Tesla'),
        ('郭明輝', '0911001017', None, '新北市三重區重新路100號', 'M', '1976-06-18', 'phone', 'normal', '["國產"]', '預算固定'),
        ('蕭美惠', '0911001018', 'hsiao.mh@mail.com', '桃園市桃園區中正路300號', 'F', '1987-09-10', 'referral', 'normal', '["進口"]', '王大明介紹'),
        ('曾俊豪', '0911001019', None, '台中市北區三民路150號', 'M', '1983-04-05', 'walk_in', 'normal', '["四驅"]', '戶外活動多'),
        ('謝雅文', '0911001020', 'hsieh.yw@mail.com', '高雄市鼓山區美術東路50號', 'F', '1996-07-20', 'line', 'potential', '["敞篷"]', '夢想車'),
        ('呂建民', '0911001021', None, '台北市中山區南京東路200號', 'M', '1972-02-28', 'web', 'vip', '["豪華"]', '換車週期2年'),
        ('簡淑玲', '0911001022', 'chien.sl@mail.com', '新北市永和區中正路150號', 'F', '1989-11-15', 'facebook', 'normal', '["安全"]', 'Volvo 粉絲'),
        ('范志偉', '0911001023', None, '桃園市龜山區萬壽路80號', 'M', '1981-07-07', 'phone', 'normal', '["旅行車"]', '長途出差多'),
        ('溫慧玲', '0911001024', 'wen.hl@mail.com', '台中市南屯區公益路350號', 'F', '1994-03-18', 'walk_in', 'potential', '["小型SUV"]', '預算50萬'),
        ('羅志祥', '0911001025', None, '台南市中西區民生路120號', 'M', '1979-06-25', 'referral', 'normal', '["柴油"]', '省油考量'),
        ('鍾美珠', '0911001026', 'chung.mc@mail.com', '新竹縣竹北市光明路100號', 'F', '1986-08-30', 'line', 'normal', '["油電"]', '環保意識強'),
        ('方大同', '0911001027', None, '台北市松山區民生東路500號', 'M', '1974-10-12', 'walk_in', 'vip', '["雙B","換車"]', '每年換車'),
        ('紀淑芳', '0911001028', 'chi.sf@mail.com', '新北市汐止區大同路200號', 'F', '1990-01-05', 'web', 'normal', '["家用"]', '小家庭'),
        ('潘建良', '0911001029', None, '桃園市蘆竹區南崁路150號', 'M', '1977-04-20', 'phone', 'cold', '["考慮中"]', '猶豫不決'),
        ('葉秀蘭', '0911001030', 'yeh.sl@mail.com', '台中市東區十甲路80號', 'F', '1983-12-08', 'facebook', 'normal', '["中型"]', '換車需求'),
        ('魏志明', '0911001031', None, '高雄市三民區建工路200號', 'M', '1971-09-15', 'walk_in', 'normal', '["日系"]', 'Toyota 愛好者'),
        ('任家萱', '0911001032', 'jen.hs@mail.com', '台北市內湖區成功路100號', 'F', '1997-05-22', 'line', 'potential', '["小車"]', '剛出社會'),
        ('余國強', '0911001033', None, '新北市中和區景安路300號', 'M', '1980-11-01', 'referral', 'normal', '["中古"]', '劉俊傑介紹'),
        ('施美玲', '0911001034', 'shih.ml@mail.com', '桃園市平鎮區環南路50號', 'F', '1988-06-14', 'web', 'normal', '["空間大"]', '載貨需求'),
        ('宋志遠', '0911001035', None, '新竹市香山區中華路600號', 'M', '1973-03-08', 'phone', 'cold', '[]', '僅詢價'),
        ('丁淑慧', '0911001036', 'ting.sh@mail.com', '台中市大里區中興路150號', 'F', '1991-09-28', 'facebook', 'normal', '["時尚"]', 'MINI 有興趣'),
        ('卓俊賢', '0911001037', None, '台南市北區開元路80號', 'M', '1984-07-16', 'walk_in', 'normal', '["運動"]', '想找 WRX'),
        ('柯雅雯', '0911001038', 'ke.yw@mail.com', '高雄市前鎮區中華路400號', 'F', '1993-02-10', 'line', 'potential', '["掀背"]', 'Focus/Mazda3'),
        ('湯明德', '0911001039', None, '嘉義市東區忠孝路200號', 'M', '1969-08-05', 'phone', 'normal', '["大型"]', '換休旅車'),
        ('程曉萍', '0911001040', 'cheng.hp@mail.com', '宜蘭縣羅東鎮中正路100號', 'F', '1986-04-22', 'referral', 'normal', '["安全","家用"]', '蕭美惠介紹'),
        ('段建中', '0911001041', None, '花蓮市國聯路50號', 'M', '1978-12-18', 'walk_in', 'normal', '["皮卡"]', '農用需求'),
        ('江淑珍', '0911001042', 'chiang.sc@mail.com', '台北市文山區興隆路300號', 'F', '1992-10-30', 'web', 'normal', '["都會"]', '停車方便'),
        ('賴國良', '0911001043', None, '新北市新店區中正路250號', 'M', '1975-05-12', 'facebook', 'vip', '["換車"]', '高管'),
        ('廖雅琴', '0911001044', 'liao.yc@mail.com', '桃園市八德區介壽路180號', 'F', '1987-01-25', 'line', 'normal', '["經濟"]', '省錢至上'),
        ('侯志龍', '0911001045', None, '台中市豐原區中正路400號', 'M', '1982-06-08', 'phone', 'normal', '["越野"]', 'Jimny 粉'),
        ('洪秀玲', '0911001046', 'hung.sl@mail.com', '台南市安平區安平路200號', 'F', '1995-08-15', 'walk_in', 'potential', '["新車比較"]', '猶豫新舊車'),
        ('姚建宏', '0911001047', None, '高雄市楠梓區楠梓路100號', 'M', '1970-11-20', 'referral', 'normal', '["商用"]', '公司添車'),
        ('白淑芬', '0911001048', 'pai.sf@mail.com', '新竹市東區食品路50號', 'F', '1989-07-03', 'web', 'normal', '["掀背","日系"]', 'Fit/Yaris'),
        ('田志豪', '0911001049', None, '彰化縣員林市中山路300號', 'M', '1976-09-12', 'walk_in', 'cold', '[]', '看了就走'),
        ('畢雅慧', '0911001050', 'pi.yh@mail.com', '基隆市安樂區基金路100號', 'F', '1994-12-28', 'facebook', 'potential', '["小型"]', '考慮中'),
    ]

    for i, cust in enumerate(customer_data):
        name, phone, email, address, gender, birthday, source, level, tags, notes = cust
        base_day = int(total_days * i / len(customer_data))
        offset = random.randint(-10, 10)
        day_offset = max(0, min(total_days - 1, base_day + offset))
        created = start_date + timedelta(days=day_offset)
        assigned = random.choice(sales_ids)

        c.execute("""INSERT INTO customers
            (name, phone, phone2, line_id, email, address, gender, birthday,
             source, level, tags, notes, total_deals, total_amount,
             last_contact, next_followup, assigned_to,
             created_at, updated_at, status)
            VALUES (?,?,NULL,NULL,?,?,?,?,?,?,?,?,0,0,?,?,?,?,?,'active')""",
            (name, phone, email, address, gender, birthday,
             source, level, tags, notes,
             created.strftime('%Y-%m-%d'),
             (created + timedelta(days=random.randint(3, 14))).strftime('%Y-%m-%d'),
             assigned,
             created.strftime('%Y-%m-%d %H:%M:%S'),
             created.strftime('%Y-%m-%d %H:%M:%S')))

    # ================================================================
    # 3. 車輛資料（60 筆）
    # ================================================================
    brands_models = [
        ('Toyota', 'Camry 2.5', 2494, 680000, 820000),
        ('Toyota', 'RAV4 2.0', 1987, 720000, 880000),
        ('Toyota', 'Yaris', 1496, 350000, 450000),
        ('Toyota', 'Corolla Cross', 1798, 620000, 750000),
        ('Toyota', 'Altis 1.8', 1798, 420000, 550000),
        ('Honda', 'CR-V 1.5T', 1498, 750000, 880000),
        ('Honda', 'Fit', 1497, 380000, 480000),
        ('Honda', 'HR-V', 1498, 580000, 680000),
        ('Honda', 'Civic 1.5T', 1498, 650000, 780000),
        ('Mazda', 'CX-5 2.0', 1998, 600000, 750000),
        ('Mazda', 'Mazda3', 1998, 520000, 650000),
        ('Mazda', 'CX-30', 1998, 550000, 680000),
        ('Nissan', 'Kicks', 1498, 420000, 520000),
        ('Nissan', 'X-Trail', 1997, 580000, 700000),
        ('BMW', '320i M Sport', 1998, 950000, 1180000),
        ('BMW', 'X1 sDrive', 1499, 880000, 1050000),
        ('BMW', '520i', 1998, 1200000, 1450000),
        ('Mercedes-Benz', 'C200', 1497, 1050000, 1280000),
        ('Mercedes-Benz', 'GLC 200', 1991, 1350000, 1580000),
        ('Mercedes-Benz', 'A200', 1332, 900000, 1080000),
        ('Volkswagen', 'Tiguan', 1498, 650000, 800000),
        ('Volkswagen', 'Golf 1.4T', 1395, 520000, 650000),
        ('Subaru', 'Forester', 1995, 580000, 720000),
        ('Volvo', 'XC40', 1969, 850000, 1020000),
        ('Lexus', 'NX 200', 1998, 1100000, 1300000),
        ('Hyundai', 'Tucson L', 1598, 580000, 700000),
        ('Mitsubishi', 'Outlander', 2360, 480000, 600000),
        ('Ford', 'Focus 1.5T', 1498, 420000, 550000),
        ('Suzuki', 'Jimny', 1462, 650000, 800000),
        ('MG', 'HS', 1490, 480000, 600000),
    ]

    colors = ['白色', '黑色', '銀色', '灰色', '藍色', '紅色']
    years = [2019, 2020, 2021, 2022, 2023, 2024]
    purchase_sources = ['個人車主', '車商交換', '法拍車', '租賃回收', '原廠認證']
    features_pool = [
        '["倒車雷達","定速"]', '["天窗","定速"]', '["CarPlay","倒車影像"]',
        '["環景","電動座椅"]', '["LED頭燈","ACC"]', '["BOSE音響","通風座椅"]',
        '["HUD","電動尾門"]', '["全景天窗","柏林之音"]', '["M套件","哈曼卡頓"]',
        '["TSS 2.0","四驅"]', '["Honda Sensing","盲點"]', '["i-Activsense"]',
    ]

    vehicle_records = []
    for vid in range(1, 61):
        bm = random.choice(brands_models)
        brand, model, cc, base_cost, base_ask = bm
        year = random.choice(years)
        color = random.choice(colors)
        mileage = random.randint(5000, 90000)
        purchase_price = base_cost + random.randint(-50000, 50000)
        repair = random.randint(5000, 80000)
        total_cost = purchase_price + repair
        asking = base_ask + random.randint(-30000, 60000)
        min_price = asking - random.randint(30000, 80000)
        features = random.choice(features_pool)
        source = random.choice(purchase_sources)

        purchase_day = random.randint(0, total_days - 30)
        purchase_date = start_date + timedelta(days=purchase_day)

        plate = (f"{''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ', k=3))}"
                 f"-{random.randint(1000, 9999)}")

        if vid <= 36:
            status = 'sold'
            sold_days_after = random.randint(7, 60)
            sold_date = purchase_date + timedelta(days=sold_days_after)
            if sold_date > end_date:
                sold_date = end_date - timedelta(days=random.randint(1, 10))
            sold_price = asking - random.randint(0, 50000)
            sold_to = random.randint(1, 50)
            location = random.choice(['展場 A', '展場 B', '展場 C'])
        elif vid <= 52:
            status = 'in_stock'
            sold_date = sold_price = sold_to = None
            location = random.choice(['展場 A', '展場 B', '展場 C'])
        elif vid <= 57:
            status = 'reserved'
            sold_date = sold_price = sold_to = None
            location = random.choice(['展場 A', '展場 B'])
        else:
            status = 'in_stock'
            sold_date = sold_price = sold_to = None
            location = '整備區'

        created_by = random.choice(all_staff_ids)
        vehicle_records.append({
            'id': vid, 'brand': brand, 'model': model,
            'total_cost': total_cost, 'asking': asking,
            'sold_date': sold_date, 'sold_price': sold_price,
            'sold_to': sold_to, 'purchase_date': purchase_date,
        })

        c.execute("""INSERT INTO vehicles
            (plate, brand, model, year, color, mileage, engine_cc, fuel_type,
             transmission, vin, purchase_date, purchase_price, purchase_from,
             repair_cost, total_cost, asking_price, min_price, photos, features,
             condition_notes, location, status, sold_date, sold_price, sold_to,
             created_by, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,'汽油','自排',NULL,?,?,?,?,?,?,?,'[]',?,?,?,?,?,?,?,?,?,?)""",
            (plate, brand, model, year, color, mileage, cc,
             purchase_date.strftime('%Y-%m-%d'), purchase_price, source,
             repair, total_cost, asking, min_price, features,
             f'{brand} {model} {year}年 {color} 車況良好',
             location, status,
             sold_date.strftime('%Y-%m-%d') if sold_date else None,
             sold_price, sold_to, created_by,
             purchase_date.strftime('%Y-%m-%d %H:%M:%S'),
             (sold_date or purchase_date).strftime('%Y-%m-%d %H:%M:%S')))

    # ================================================================
    # 4. 交易（36 售出 + 14 收購 = 50 筆）
    # ================================================================
    for vr in vehicle_records[:36]:
        profit = (vr['sold_price'] or vr['asking']) - vr['total_cost']
        payment = random.choice(['現金', '匯款', '分期', '刷卡'])
        seller = random.choice(sales_ids)
        deal_date = vr['sold_date'] or vr['purchase_date'] + timedelta(days=30)

        c.execute("""INSERT INTO deals
            (deal_type, customer_id, vehicle_id, amount, cost, profit,
             payment_method, payment_status, deal_date, notes, documents,
             created_by, created_at, status)
            VALUES ('sell',?,?,?,?,?,?,'paid',?,?,'[]',?,?,'completed')""",
            (vr['sold_to'], vr['id'], vr['sold_price'],
             vr['total_cost'], profit, payment,
             deal_date.strftime('%Y-%m-%d'),
             f"{vr['brand']} {vr['model']} 售出",
             seller, deal_date.strftime('%Y-%m-%d %H:%M:%S')))

    for month in range(14):
        buy_date = start_date + timedelta(days=month * 30 + random.randint(0, 15))
        if buy_date > end_date:
            break
        amount = random.randint(200000, 800000)
        c.execute("""INSERT INTO deals
            (deal_type, customer_id, vehicle_id, amount, cost, profit,
             payment_method, payment_status, deal_date, notes, documents,
             created_by, created_at, status)
            VALUES ('buy',?,NULL,?,?,0,?,'paid',?,?,'[]',?,?,'completed')""",
            (random.randint(1, 50), amount, amount,
             random.choice(['現金', '匯款']),
             buy_date.strftime('%Y-%m-%d'), '收購客戶車輛',
             random.choice(all_staff_ids[:3]),
             buy_date.strftime('%Y-%m-%d %H:%M:%S')))

    # 更新客戶統計
    c.execute("""UPDATE customers SET
        total_deals = (SELECT COUNT(*) FROM deals WHERE deals.customer_id = customers.id),
        total_amount = COALESCE((SELECT SUM(amount) FROM deals
                        WHERE deals.customer_id = customers.id), 0)""")

    # ================================================================
    # 5. 跟進記錄（200 筆）
    # ================================================================
    followup_contents = {
        'call': ['電話詢問車況，已報價', '回電確認試駕時間', '電話跟進購車意願',
                 '通知新到車輛', '確認付款方式', '售後關懷電話',
                 '電話預約保養', '詢問換車需求', '確認交車時間'],
        'line': ['LINE 傳送車輛照片', '客戶 LINE 詢問庫存', 'LINE 確認到店時間',
                 'LINE 傳送報價單', '回覆車輛規格詢問', 'LINE 分享優惠活動'],
        'visit': ['客戶到店看車', '試駕體驗', '到店簽約', '到店交車',
                  '帶家人來看車', '二次到店比較車款'],
        'sms': ['簡訊通知促銷活動', '簡訊提醒保養到期', '簡訊確認預約'],
    }
    results = ['有興趣', '考慮中', '暫不需要', '已預約試駕', '已成交', '待跟進', None]
    next_actions = ['再次電話', '安排試駕', '發送報價', '等客戶回覆', None]

    for _ in range(200):
        ftype = random.choice(['call', 'line', 'visit', 'sms'])
        content = random.choice(followup_contents[ftype])
        result = random.choice(results)
        day_offset = random.randint(0, total_days)
        created = start_date + timedelta(days=day_offset,
                                         hours=random.randint(9, 18),
                                         minutes=random.randint(0, 59))
        na = random.choice(next_actions)
        nd = (created + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d') if na else None

        c.execute("""INSERT INTO followups
            (customer_id, vehicle_id, user_id, type, content, result,
             next_action, next_date, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (random.randint(1, 50),
             random.randint(1, 60) if random.random() > 0.3 else None,
             random.choice(sales_ids), ftype, content, result,
             na, nd, created.strftime('%Y-%m-%d %H:%M:%S')))

    # ================================================================
    # 6. 活動日誌（300 筆）
    # ================================================================
    log_actions = [
        ('login', '系統', '登入系統'),
        ('create_customer', '客戶', '新增客戶'),
        ('update_customer', '客戶', '更新客戶資料'),
        ('create_vehicle', '車輛', '新增車輛'),
        ('update_vehicle', '車輛', '更新車輛資料'),
        ('create_deal', '交易', '建立交易'),
        ('create_followup', '跟進', '新增跟進記錄'),
        ('view_report', '報表', '查看報表'),
        ('export_data', '報表', '匯出資料'),
    ]
    staff_names = {1: '陳永發', 2: '林志明', 3: '張美華',
                   4: '王建志', 5: '李佳蓉', 6: '黃志豪'}

    for _ in range(300):
        uid = random.choice(all_staff_ids)
        action, target_type, details = random.choice(log_actions)
        day_offset = random.randint(0, total_days)
        created = start_date + timedelta(days=day_offset,
                                         hours=random.randint(8, 19),
                                         minutes=random.randint(0, 59))
        c.execute("""INSERT INTO activity_logs
            (user_id, user_name, action, target_type, target_id, target_name,
             details, ip_address, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (uid, staff_names[uid], action, target_type,
             random.randint(1, 50), None, details,
             f'192.168.1.{random.randint(10, 99)}',
             created.strftime('%Y-%m-%d %H:%M:%S')))

    # ================================================================
    # 7. 系統設定
    # ================================================================
    for key, value in [
        ('shop_name', '永發中古車行'),
        ('shop_address', '台北市中山區民權東路100號'),
        ('shop_phone', '02-25001234'),
        ('shop_line', '@yongfa-cars'),
        ('business_hours', '09:00-21:00'),
        ('db_version', '2'),
    ]:
        c.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?,?,CURRENT_TIMESTAMP)", (key, value))

    # 更新客戶最後聯繫時間
    c.execute("""UPDATE customers SET
        last_contact = (SELECT MAX(created_at) FROM followups
                        WHERE followups.customer_id = customers.id),
        updated_at = CURRENT_TIMESTAMP""")

    conn.commit()
    conn.close()

    print("✅ 展示資料載入完成：")
    print("   👤 人員：1 老闆 + 2 經理 + 3 業務")
    print("   🧑 客戶：50 筆")
    print("   🚗 車輛：60 筆（36已售/16在庫/5預留/3整備）")
    print("   💰 交易：50 筆（36售出+14收購）")
    print("   📞 跟進：200 筆")
    print("   📋 日誌：300 筆")
    print("   📅 期間：2025/01 ~ 2026/02")
