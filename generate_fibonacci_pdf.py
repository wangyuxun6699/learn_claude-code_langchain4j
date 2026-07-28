#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成斐波那契数列研究 PDF
使用 fpdf2 + Windows 中文字体
"""

from fpdf import FPDF

class FibonacciPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        # 注册中文字体
        self.add_font('SimHei', '', r'C:\Windows\Fonts\simhei.ttf')
        self.add_font('SimSun', '', r'C:\Windows\Fonts\simsun.ttc')
        self.add_font('SimKai', '', r'C:\Windows\Fonts\simkai.ttf')
        self.add_font('SimFang', '', r'C:\Windows\Fonts\simfang.ttf')
        self.set_auto_page_break(True, 20)

    def cover_page(self):
        """生成封面"""
        self.add_page()
        self.ln(50)
        # 装饰线
        self.set_draw_color(139, 69, 19)
        self.set_line_width(0.8)
        self.line(30, self.get_y(), 180, self.get_y())
        self.ln(10)

        # 标题
        self.set_font('SimHei', '', 32)
        self.set_text_color(139, 69, 19)
        self.cell(0, 15, '斐波那契数列研究', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

        # 副标题
        self.set_font('SimKai', '', 16)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, '—— 从数学之美到自然之韵', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(8)

        self.set_draw_color(139, 69, 19)
        self.line(30, self.get_y(), 180, self.get_y())
        self.ln(15)

        # 黄金螺旋示意图（用文字描述）
        self.set_font('SimSun', '', 11)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, 'Fibonacci Sequence Research', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(20)

        # 信息
        self.set_font('SimSun', '', 12)
        self.set_text_color(60, 60, 60)
        info_lines = [
            '涵盖内容：数列定义 | 数学性质 | 黄金比例 | 自然界实例 | 应用领域',
            '',
            '2025 年 1 月',
        ]
        for line in info_lines:
            self.cell(0, 8, line, align='C', new_x="LMARGIN", new_y="NEXT")

    def chapter_title(self, num, title):
        """章节标题"""
        self.ln(5)
        self.set_font('SimHei', '', 18)
        self.set_text_color(139, 69, 19)
        self.cell(0, 10, f'第{num}章  {title}', new_x="LMARGIN", new_y="NEXT")
        # 装饰线
        self.set_draw_color(139, 69, 19)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y() + 2, self.w - self.r_margin, self.get_y() + 2)
        self.ln(8)

    def section_title(self, title):
        """小节标题"""
        self.ln(3)
        self.set_font('SimHei', '', 13)
        self.set_text_color(80, 50, 20)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        """正文段落"""
        self.set_font('SimSun', '', 11)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 7, text, align='L')
        self.ln(2)

    def formula_block(self, formula, center=True):
        """公式块"""
        self.ln(1)
        self.set_font('SimSun', '', 12)
        self.set_text_color(0, 80, 130)
        if center:
            self.cell(0, 8, formula, align='C', new_x="LMARGIN", new_y="NEXT")
        else:
            self.cell(0, 8, formula, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def sequence_display(self, label, values):
        """数列展示"""
        self.set_font('SimSun', '', 11)
        self.set_text_color(40, 40, 40)
        self.cell(0, 7, f'{label}：{values}', new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def table_fibonacci(self, n_values):
        """制作斐波那契数列表格"""
        self.set_font('SimSun', '', 10)
        col_w = (self.w - self.l_margin - self.r_margin) / 5
        # 表头
        self.set_fill_color(139, 69, 19)
        self.set_text_color(255, 255, 255)
        headers = ['n', 'F(n)', 'F(n-1)/F(n)', 'F(n)/F(n-1)', 'F(n+1)/F(n)']
        for h in headers:
            self.cell(col_w, 8, h, border=1, align='C', fill=True)
        self.ln()

        # 数据行
        self.set_text_color(40, 40, 40)
        fibs = [0, 1]
        for i in range(2, max(n_values) + 2):
            fibs.append(fibs[i-1] + fibs[i-2])

        for i, n in enumerate(n_values):
            if i % 2 == 0:
                self.set_fill_color(250, 245, 235)
            else:
                self.set_fill_color(255, 255, 255)

            fn = fibs[n]
            ratio1 = f"{fibs[n-1]/fn:.6f}" if n > 0 and fn != 0 else "N/A"
            ratio2 = f"{fn/fibs[n-1]:.6f}" if n > 0 and fibs[n-1] != 0 else "N/A"
            ratio3 = f"{fibs[n+1]/fn:.6f}" if n > 0 and fn != 0 else "N/A"

            data = [str(n), str(fn), str(ratio1), str(ratio2), str(ratio3)]
            for d in data:
                self.cell(col_w, 7, d, border=1, align='C', fill=True)
            self.ln()
        self.ln(2)

def generate_pdf():
    pdf = FibonacciPDF()

    # ==================== 封面 ====================
    pdf.cover_page()

    # ==================== 目录页 ====================
    pdf.add_page()
    pdf.set_font('SimHei', '', 22)
    pdf.set_text_color(139, 69, 19)
    pdf.cell(0, 12, '目  录', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(12)

    toc = [
        ('一', '斐波那契数列的定义与起源', 3),
        ('二', '斐波那契数列的数学性质', 5),
        ('三', '黄金比例——斐波那契数列的灵魂', 8),
        ('四', '斐波那契数列在自然界中的呈现', 10),
        ('五', '斐波那契数列的应用', 13),
        ('六', '总结与展望', 16),
    ]

    pdf.set_font('SimSun', '', 13)
    pdf.set_text_color(40, 40, 40)
    for num, title, page in toc:
        pdf.cell(10, 9, f'{num}.', align='C')
        pdf.cell(0, 9, f'{title}', align='L')
        pdf.ln()

    # ==================== 第一章 ====================
    pdf.add_page()
    pdf.chapter_title('一', '斐波那契数列的定义与起源')

    pdf.section_title('1.1  历史背景')
    pdf.body_text(
        '斐波那契数列（Fibonacci sequence）以意大利数学家列昂纳多·斐波那契（Leonardo Fibonacci，约1170—1250年）'
        '的名字命名。斐波那契是中世纪欧洲最杰出的数学家之一，他在1202年出版的著作《计算之书》（Liber Abaci）中，'
        '首次将印度-阿拉伯数字系统引入欧洲，并在其中提出了著名的"兔子繁殖问题"，从而引出了这一经典数列。'
    )
    pdf.body_text(
        '值得注意的是，斐波那契数列并非斐波那契本人首次发现。早在公元前200年左右，印度数学家平加拉（Pingala）'
        '在研究梵文诗歌韵律时就涉及了该数列。后来的印度数学家维拉汉卡（Virahanka，约公元700年）和戈帕拉（Gopala，'
        '约公元1135年）也独立研究了这一数列。然而，斐波那契是第一个向欧洲世界系统介绍这一数列的人，因此该数列'
        '在西方世界以他的名字命名。'
    )

    pdf.section_title('1.2  兔子繁殖问题')
    pdf.body_text(
        '斐波那契在《计算之书》中提出了以下问题：假设一对刚出生的兔子（一雄一雌）被放到一个封闭的场地中。'
        '兔子在出生后第二个月开始具备繁殖能力，此后每月都能生一对兔子（一雄一雌）。所有兔子均不会死亡。'
        '问：从最初的一对兔子开始，经过n个月后，共有多少对兔子？'
    )
    pdf.body_text(
        '分析这一过程可以发现：第1个月，只有最初的一对兔子（刚出生，尚不能繁殖）。第2个月，最初的那对兔子成年，'
        '共有1对。第3个月，最初的那对兔子生育一对新兔子，共有2对。第4个月，最初的那对兔子再次生育，而第3个月'
        '出生的兔子尚未成年，因此共有3对。以此类推，每月兔子对数形成的数列就是斐波那契数列。'
    )

    pdf.section_title('1.3  数列的递归定义')
    pdf.body_text(
        '斐波那契数列的数学定义非常简洁。用F(n)表示第n个斐波那契数，其递归定义为：'
    )
    pdf.formula_block('F(0) = 0,  F(1) = 1')
    pdf.formula_block('F(n) = F(n-1) + F(n-2),   当 n ≥ 2')

    pdf.body_text(
        '也就是说，从第三项起，每一项都等于前两项之和。按照这一定义，斐波那契数列的前若干项为：'
    )
    pdf.sequence_display('斐波那契数列前15项', '0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, ...')

    # ==================== 第二章 ====================
    pdf.add_page()
    pdf.chapter_title('二', '斐波那契数列的数学性质')

    pdf.section_title('2.1  通项公式——比内公式')
    pdf.body_text(
        '虽然斐波那契数列是递归定义的，但它也有一个封闭形式的通项公式，称为比内公式（Binet\'s Formula），'
        '由法国数学家雅克·菲利普·马里·比内（Jacques Philippe Marie Binet）于1843年推导得出。'
        '该公式用黄金比例φ（phi）及其共轭ψ（psi）来表达任意斐波那契数：'
    )
    pdf.formula_block('令  φ = (1 + √5) / 2 ≈ 1.6180339887...')
    pdf.formula_block('    ψ = (1 - √5) / 2 ≈ -0.6180339887...')
    pdf.ln(2)
    pdf.formula_block('F(n) = (φⁿ - ψⁿ) / √5')
    pdf.body_text(
        '这个公式的美妙之处在于，它完全由无理数φ和ψ构成，但计算出的结果却总是整数。'
        '此外，由于|ψ| < 1，当n很大时ψⁿ趋近于0，因此F(n)约等于φⁿ/√5，而且F(n)恰好是最接近φⁿ/√5的整数。'
    )

    pdf.section_title('2.2  与黄金比例的关系')
    pdf.body_text(
        '斐波那契数列与黄金比例φ之间存在着深刻的联系。当数列的项数趋向无穷大时，相邻两项的比值收敛于黄金比例：'
    )
    pdf.formula_block('lim_{n→∞} F(n+1) / F(n) = φ ≈ 1.618034')
    pdf.body_text(
        '下表展示了随着n增大，相邻斐波那契数之比逐渐逼近黄金比例的过程：'
    )

    # 插入表格
    pdf.table_fibonacci([1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20])

    pdf.section_title('2.3  卡西尼恒等式')
    pdf.body_text(
        '卡西尼恒等式（Cassini\'s Identity）由法国天文学家乔瓦尼·卡西尼（Giovanni Domenico Cassini）于1680年发现，'
        '揭示了斐波那契数列中三个连续项之间的优美关系：'
    )
    pdf.formula_block('F(n-1) · F(n+1) - F(n)² = (-1)ⁿ')
    pdf.body_text(
        '例如，取n=5：F(4)×F(6) - F(5)² = 3×8 - 5² = 24 - 25 = (-1)⁵ = -1。'
        '这个恒等式是卡塔兰猜想（Catalan\'s Conjecture，即后来的Mihăilescu定理）的二维类比基础。'
    )

    pdf.section_title('2.4  其他重要性质')
    properties = [
        ('整除性质：', '如果m整除n，则F(m)整除F(n)。例如，F(3)=2整除F(6)=8，F(4)=3整除F(8)=21。'),
        ('最大公约数性质：', 'gcd(F(m), F(n)) = F(gcd(m, n))。这一性质使得斐波那契数在数论中具有特殊地位。'),
        ('平方和性质：', 'F(1)² + F(2)² + ... + F(n)² = F(n) × F(n+1)。前n个斐波那契数的平方和等于第n个与第n+1个的乘积。'),
        ('相邻项互质性：', '任意两个相邻的斐波那契数互质，即gcd(F(n), F(n+1)) = 1。'),
        ('奇数项之和：', 'F(1) + F(3) + ... + F(2n-1) = F(2n)。'),
        ('偶数项之和：', 'F(2) + F(4) + ... + F(2n) = F(2n+1) - 1。'),
    ]
    for title, desc in properties:
        pdf.set_font('SimHei', '', 11)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(35, 7, title)
        pdf.set_font('SimSun', '', 11)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 7, desc)
        pdf.ln(1)

    # ==================== 第三章 ====================
    pdf.add_page()
    pdf.chapter_title('三', '黄金比例——斐波那契数列的灵魂')

    pdf.section_title('3.1  黄金比例的定义与历史')
    pdf.body_text(
        '黄金比例（Golden Ratio），通常用希腊字母φ（phi）表示，其值约为1.6180339887。这一比例的定义是：'
        '将一条线段分成两部分，使得全长与较长部分之比等于较长部分与较短部分之比。从代数的角度看，'
        '如果较长部分为a，较短部分为b（a > b > 0），则：'
    )
    pdf.formula_block('(a+b) / a = a / b = φ')
    pdf.body_text(
        '解这个方程可得φ = (1+√5)/2 ≈ 1.618，这是二次方程x² - x - 1 = 0的正根。'
        '黄金比例的概念可以追溯到古希腊时期。欧几里得在《几何原本》中将其称为"极端与平均之比"。'
        '文艺复兴时期，卢卡·帕乔利（Luca Pacioli）在其著作《神圣比例》（De Divina Proportione，1509年）'
        '中深入研究了这一比例，该书由达·芬奇绘制插图。'
    )

    pdf.section_title('3.2  黄金比例的数学性质')
    pdf.body_text(
        '黄金比例具有许多独特的数学性质，使其成为数学中最迷人的常数之一：'
    )
    props_golden = [
        'φ² = φ + 1 — 黄金比例是唯一一个平方等于自身加1的正数。',
        '1/φ = φ - 1 ≈ 0.618 — 黄金比例的倒数等于它自身减1。',
        'φⁿ = F(n)·φ + F(n-1) — 黄金比例的幂可以用斐波那契数线性表示。',
        '连分数表示：φ = [1; 1, 1, 1, ...]，是所有连分数中收敛最慢的，因此被称为"最无理的"无理数。',
        '连根式表示：φ = √(1 + √(1 + √(1 + ...)))。',
        '在正五边形中，对角线长度与边长之比恰好是黄金比例。',
    ]
    for p in props_golden:
        pdf.set_font('SimSun', '', 11)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(8, 7, '▸ ')
        pdf.multi_cell(0, 7, p)
        pdf.ln(1)

    pdf.section_title('3.3  黄金矩形与黄金螺旋')
    pdf.body_text(
        '长宽比为φ:1的矩形称为黄金矩形（Golden Rectangle）。黄金矩形的一个独特性质是：'
        '从中切去一个正方形后，剩余的小矩形仍然是一个黄金矩形。这一过程可以无限进行下去，'
        '在每个正方形内画出四分之一圆弧，连接起来就形成了优美的黄金螺旋（Golden Spiral）。'
    )
    pdf.body_text(
        '黄金螺旋是对数螺旋的一种近似，广泛存在于自然界中——鹦鹉螺的壳、飓风的形状、'
        '旋涡星系的旋臂结构等都呈现出对数螺旋的特征。'
    )

    # ==================== 第四章 ====================
    pdf.add_page()
    pdf.chapter_title('四', '斐波那契数列在自然界中的呈现')

    pdf.section_title('4.1  植物的叶序与花序')
    pdf.body_text(
        '植物学中的"叶序"（Phyllotaxis）研究叶片在茎上的排列方式。许多植物的叶片以螺旋状排列，'
        '相邻叶片之间的角度约为137.5°，这恰好是360°/φ²，被称为"黄金角"（Golden Angle）。'
        '这种排列方式使得每片叶子都能最大限度地接受阳光照射，避免被上方的叶子遮挡。'
    )
    pdf.body_text(
        '向日葵的花盘是斐波那契数列最著名的自然实例之一。向日葵的种子排列成两组螺旋线：'
        '顺时针螺旋和逆时针螺旋。这两组螺旋的数量几乎总是两个相邻的斐波那契数——最常见的是'
        '34和55，较大的向日葵可以达到89和144。类似的现象也出现在松果（通常为8和13条螺旋）、'
        '菠萝（通常为8、13或21条螺旋）、雏菊和洋蓟等植物中。'
    )

    pdf.section_title('4.2  花瓣数量')
    pdf.body_text(
        '许多花卉的花瓣数量恰好是斐波那契数列中的数字。以下是一些常见的例子：'
    )
    petals = [
        '3瓣：百合、鸢尾花（部分品种）',
        '5瓣：毛茛、野玫瑰、樱花、苹果花、桃花',
        '8瓣：飞燕草（部分品种）、铁线莲',
        '13瓣：万寿菊、金盏花（部分品种）',
        '21瓣：菊苣、紫菀（部分品种）',
        '34瓣：大滨菊、雏菊（大型品种）',
        '55、89瓣：向日葵科植物（菊科）',
    ]
    for p in petals:
        pdf.set_font('SimSun', '', 11)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(8, 7, '✦ ')
        pdf.cell(0, 7, p, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.section_title('4.3  动物界的斐波那契现象')
    pdf.body_text(
        '斐波那契数列在动物界同样有着令人惊叹的体现。鹦鹉螺壳的螺旋生长模式精确地遵循着对数螺旋，'
        '其内部腔室的大小按照黄金比例递增。蜜蜂的谱系也呈现出斐波那契模式：雄蜂（由未受精卵发育而来）'
        '只有母亲而没有父亲，雌蜂（由受精卵发育而来）既有母亲也有父亲。绘制蜜蜂的谱系图时，'
        '每一代祖先的数量正好构成斐波那契数列。'
    )
    pdf.body_text(
        '此外，人体中也隐藏着黄金比例：从肚脐到脚底的距离与身高之比约为1/φ ≈ 0.618；'
        '前臂与上臂的长度比、手指各节之间的比例都接近黄金比例。'
        '达·芬奇的著名素描《维特鲁威人》（Vitruvian Man）正是对人体黄金比例的完美呈现。'
    )

    # ==================== 第五章 ====================
    pdf.add_page()
    pdf.chapter_title('五', '斐波那契数列的应用')

    pdf.section_title('5.1  计算机科学与算法')
    pdf.body_text(
        '斐波那契数列在计算机科学中有着广泛而深入的应用。斐波那契堆（Fibonacci Heap）是'
        '一种高效的数据结构，由Michael L. Fredman和Robert E. Tarjan于1984年提出，在Dijkstra最短路径算法'
        '和Prim最小生成树算法中能够获得更优的摊销时间复杂度。'
    )
    pdf.body_text(
        '斐波那契搜索（Fibonacci Search）是一种用于在有序数组中查找元素的算法，其分割策略基于'
        '斐波那契数，在某些情况下比二分搜索更为高效。此外，斐波那契编码（Fibonacci Coding）'
        '是一种使用斐波那契数的通用编码方案，被用于数据压缩和信息论中。'
    )
    pdf.body_text(
        '动态规划教材中，斐波那契数列的递归计算是讲解记忆化（Memoization）和重叠子问题'
        '的经典范例。朴素的递归算法时间复杂度为O(2ⁿ)，而使用记忆化或自底向上的迭代方法'
        '可以将时间复杂度降至O(n)，使用矩阵快速幂方法甚至可以降至O(log n)。'
    )

    pdf.section_title('5.2  金融市场与技术分析')
    pdf.body_text(
        '在金融技术分析领域，斐波那契回调（Fibonacci Retracement）是一种广泛使用的工具。'
        '交易者通过在高点和低点之间画出斐波那契比例水平线（23.6%、38.2%、50%、61.8%、78.6%），'
        '来预测价格回调的可能支撑位和阻力位。其中，61.8%（即1/φ）被认为是最重要的斐波那契'
        '回调水平。斐波那契扩展（Fibonacci Extension）则用于预测趋势延续时的目标价位。'
    )
    pdf.body_text(
        '拉尔夫·纳尔逊·艾略特（Ralph Nelson Elliott）在1930年代提出的艾略特波浪理论'
        '（Elliott Wave Theory）同样深受斐波那契数列的影响。该理论认为市场价格的波动遵循'
        '特定的模式：一个完整的市场周期包含8个浪（5个推动浪+3个调整浪），而这些波浪的数量'
        '和幅度与斐波那契数列紧密相关。'
    )

    pdf.section_title('5.3  艺术与建筑')
    pdf.body_text(
        '黄金比例自古以来就被艺术家和建筑师视为美的标准。古希腊的帕特农神庙（Parthenon）的'
        '正面比例、古埃及的吉萨大金字塔的斜面三角形比例都近似于黄金比例。文艺复兴时期的'
        '艺术家如达·芬奇、米开朗基罗和拉斐尔都在他们的作品中广泛使用黄金比例进行构图。'
        '现代设计领域，从苹果公司的Logo到Twitter的界面布局，黄金比例的应用无处不在。'
    )
    pdf.body_text(
        '在音乐领域，斐波那契数列同样有着惊人的应用。巴托克·贝拉（Béla Bartók）、克劳德·德彪西'
        '（Claude Debussy）等作曲家在其作品中融入了斐波那契数列的结构。钢琴键盘上一个人度包含'
        '13个音符（8个白键和5个黑键），而8和5恰好是两个相邻的斐波那契数。'
    )

    pdf.section_title('5.4  密码学与编码理论')
    pdf.body_text(
        '斐波那契数列在密码学中也有应用。基于斐波那契数的伪随机数生成器可以用于流密码系统。'
        '斐波那契线性反馈移位寄存器（LFSR）是序列密码的基本构件之一。此外，斐波那契数列在'
        '某些公钥密码体制的构造中也被使用，例如基于斐波那契数的背包密码系统。'
    )

    # ==================== 第六章 ====================
    pdf.add_page()
    pdf.chapter_title('六', '总结与展望')

    pdf.body_text(
        '斐波那契数列是数学中最迷人的序列之一。从1202年一个看似简单的兔子繁殖问题出发，'
        '它已经发展成为连接数论、组合数学、计算理论、自然科学乃至艺术美学的一条金线。'
        '它的魅力在于其定义的简单性与性质的深刻性之间的巨大反差——只需"前两项之和"这五个字'
        '就能定义，但其中蕴含的数学结构和自然规律却无穷无尽。'
    )

    pdf.section_title('6.1  斐波那契数列的推广')
    pdf.body_text(
        '数学家们对斐波那契数列进行了多种推广。卢卡斯数列（Lucas Numbers）具有与斐波那契数列'
        '相同的递推关系，但初始值不同：L(0)=2, L(1)=1。广义斐波那契数列允许任意的初始值。'
        'Tribonacci数列将递推扩展为三项之和：T(n)=T(n-1)+T(n-2)+T(n-3)。'
        '此外，斐波那契数列还可以推广到负数索引、复数索引，甚至矩阵形式。'
    )

    pdf.section_title('6.2  开放问题与研究方向')
    pdf.body_text(
        '尽管斐波那契数列已被研究了八百多年，但关于它仍然存在许多未解之谜。例如：'
        '是否存在无穷多个斐波那契素数（即同时是斐波那契数又是素数的数）？目前已知的最大'
        '斐波那契素数具有数十万位数字，但该问题的一般性结论仍然未知。又如，斐波那契数列'
        '中是否包含无穷多个完全平方数？这些看似简单的问题至今仍在推动数学研究的前沿。'
    )

    pdf.section_title('6.3  结语')
    pdf.body_text(
        '斐波那契数列向我们展示了数学世界与自然世界之间深刻的内在联系。它提醒我们，'
        '在最基本的数学结构中，隐藏着宇宙运行的深层密码。从向日葵的螺旋到星系的旋臂，'
        '从计算机算法到金融市场，斐波那契数列以其优雅而神秘的方式，将数学之美深深嵌入'
        '世界的每一个角落。正如伽利略所说："自然的书是用数学语言写成的。"'
        '而斐波那契数列，无疑是这本自然之书中最华美的篇章之一。'
    )

    # ==================== 参考文献 ====================
    pdf.ln(8)
    pdf.set_draw_color(139, 69, 19)
    pdf.set_line_width(0.6)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(6)

    pdf.set_font('SimHei', '', 16)
    pdf.set_text_color(139, 69, 19)
    pdf.cell(0, 10, '参考文献', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    refs = [
        '[1]  Fibonacci, L. (1202). Liber Abaci. Pisa.',
        '[2]  Knuth, D. E. (1997). The Art of Computer Programming, Vol. 1: Fundamental Algorithms (3rd ed.). Addison-Wesley.',
        '[3]  Livio, M. (2002). The Golden Ratio: The Story of Phi, the World\'s Most Astonishing Number. Broadway Books.',
        '[4]  Vorobiev, N. N. (2002). Fibonacci Numbers. Birkhäuser Basel.',
        '[5]  Koshy, T. (2001). Fibonacci and Lucas Numbers with Applications. Wiley-Interscience.',
        '[6]  Dunlap, R. A. (1997). The Golden Ratio and Fibonacci Numbers. World Scientific.',
        '[7]  Garland, T. H. (1987). Fascinating Fibonaccis: Mystery and Magic in Numbers. Dale Seymour Publications.',
        '[8]  Posamentier, A. S. & Lehmann, I. (2007). The Fabulous Fibonacci Numbers. Prometheus Books.',
        '[9]  Huntley, H. E. (1970). The Divine Proportion: A Study in Mathematical Beauty. Dover Publications.',
        '[10] Vajda, S. (1989). Fibonacci & Lucas Numbers, and the Golden Section: Theory and Applications. Ellis Horwood.',
    ]

    pdf.set_font('SimSun', '', 10)
    pdf.set_text_color(40, 40, 40)
    for ref in refs:
        pdf.cell(0, 6.5, ref, new_x="LMARGIN", new_y="NEXT")

    # ==================== 保存 ====================
    output_path = r'D:\learn_claude_code\fibonacci_research.pdf'
    pdf.output(output_path)
    print(f'PDF 生成成功！文件路径：{output_path}')
    print(f'总页数：{pdf.pages_count}')

if __name__ == '__main__':
    generate_pdf()
