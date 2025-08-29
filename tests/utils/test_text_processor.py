from unittest.mock import patch

from utils.text_processor import parse_output_summary, format_output_summary, section_aliases


class TestTextProcessor:

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名", "症状経過", "治療経過", "現在の処方", "備考"
    ])
    def test_parse_output_summary_complete_sections(self):
        """全セクションが含まれる完全なサマリのテスト"""
        summary_text = """患者情報
田中太郎 75歳 男性

主病名
急性心筋梗塞

症状経過
胸痛にて来院。心電図でST上昇を認める。

治療経過
緊急カテーテル治療を実施。
ステント留置術を行った。

現在の処方
アスピリン 100mg 1日1回
クロピドグレル 75mg 1日1回

備考
経過良好。外来フォロー予定。"""

        result = parse_output_summary(summary_text)

        assert result["患者情報"] == "田中太郎 75歳 男性"
        assert result["主病名"] == "急性心筋梗塞"
        assert result["症状経過"] == "胸痛にて来院。心電図でST上昇を認める。"
        assert result["治療経過"] == "緊急カテーテル治療を実施。\nステント留置術を行った。"
        assert result["現在の処方"] == "アスピリン 100mg 1日1回\nクロピドグレル 75mg 1日1回"
        assert result["備考"] == "経過良好。外来フォロー予定。"

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名", "症状経過", "治療経過", "現在の処方", "備考"
    ])
    def test_parse_output_summary_with_aliases(self):
        """セクションエイリアスのテスト"""
        summary_text = """患者情報
佐藤花子 65歳 女性

病名: 糖尿病性腎症

症状
多尿、口渇

治療内容
インスリン療法開始

処方:
インスリン グラルギン 20単位

その他
血糖値モニタリング継続"""

        result = parse_output_summary(summary_text)

        assert result["患者情報"] == "佐藤花子 65歳 女性"
        assert result["主病名"] == "糖尿病性腎症"  # 病名 → 主病名
        assert result["症状経過"] == "多尿、口渇"  # 症状 → 症状経過
        assert result["治療経過"] == "インスリン療法開始"  # 治療内容 → 治療経過
        assert result["現在の処方"] == "インスリン グラルギン 20単位"  # 処方 → 現在の処方
        assert result["備考"] == "血糖値モニタリング継続"  # その他 → 備考

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名", "症状経過", "治療経過", "現在の処方", "備考"
    ])
    def test_parse_output_summary_partial_sections(self):
        """部分的なセクションのテスト"""
        summary_text = """主病名
高血圧症

治療経過
降圧薬療法を開始
ACE阻害薬を処方"""

        result = parse_output_summary(summary_text)

        assert result["主病名"] == "高血圧症"
        assert result["治療経過"] == "降圧薬療法を開始\nACE阻害薬を処方"
        # 他のセクションは空文字列
        assert result["患者情報"] == ""
        assert result["症状経過"] == ""
        assert result["現在の処方"] == ""
        assert result["備考"] == ""

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名", "症状経過", "治療経過", "現在の処方", "備考"
    ])
    def test_parse_output_summary_inline_content(self):
        """セクション名と内容が同一行にある場合のテスト"""
        summary_text = """患者情報 山田一郎 80歳 男性
主病名 慢性閉塞性肺疾患
症状経過 呼吸困難にて入院
治療経過: 酸素療法を開始。ステロイド投与。
現在の処方： プレドニゾロン 30mg
備考 在宅酸素療法導入予定"""

        result = parse_output_summary(summary_text)

        assert result["患者情報"] == "山田一郎 80歳 男性"
        assert result["主病名"] == "慢性閉塞性肺疾患"
        assert result["症状経過"] == "呼吸困難にて入院"
        assert result["治療経過"] == "酸素療法を開始。ステロイド投与。"
        assert result["現在の処方"] == "プレドニゾロン 30mg"
        assert result["備考"] == "在宅酸素療法導入予定"

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名", "症状経過"
    ])
    def test_parse_output_summary_empty_lines_handling(self):
        """空行の処理テスト"""
        summary_text = """患者情報

田中次郎 70歳 男性


主病名

肺炎


症状経過
発熱、咳嗽

呼吸困難"""

        result = parse_output_summary(summary_text)

        assert result["患者情報"] == "田中次郎 70歳 男性"
        assert result["主病名"] == "肺炎"
        assert result["症状経過"] == "発熱、咳嗽\n呼吸困難"

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名", "症状経過"
    ])
    def test_parse_output_summary_no_sections(self):
        """セクション名がない場合のテスト"""
        summary_text = """これは単なるテキストです。
セクションヘッダーがありません。
全て同じセクションとして扱われます。"""

        result = parse_output_summary(summary_text)

        # すべてのセクションが空文字列のままであることを確認
        assert result["患者情報"] == ""
        assert result["主病名"] == ""
        assert result["症状経過"] == ""

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名"
    ])
    def test_parse_output_summary_duplicate_sections(self):
        """重複するセクション名のテスト"""
        summary_text = """患者情報
最初の患者情報

主病名
心筋梗塞

患者情報
二回目の患者情報
追加の患者データ"""

        result = parse_output_summary(summary_text)

        # 最後のセクションの内容が優先される
        assert result["患者情報"] == "最初の患者情報\n二回目の患者情報\n追加の患者データ"
        assert result["主病名"] == "心筋梗塞"

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名", "症状経過"
    ])
    def test_parse_output_summary_mixed_separators(self):
        """様々な区切り文字のテスト"""
        summary_text = """患者情報:
田中三郎 55歳 男性

主病名：
狭心症

症状経過
胸部圧迫感
運動時息切れ"""

        result = parse_output_summary(summary_text)

        assert result["患者情報"] == "田中三郎 55歳 男性"
        assert result["主病名"] == "狭心症"
        assert result["症状経過"] == "胸部圧迫感\n運動時息切れ"

    def test_parse_output_summary_edge_case_long_section_content(self):
        """セクション名に長い内容が続く場合の境界テスト"""
        with patch('utils.text_processor.DEFAULT_SECTION_NAMES', ["患者情報", "主病名"]):
            # 100文字制限のテスト
            long_content = "これは非常に長い内容です。" * 5  # 約100文字以上
            summary_text = f"患者情報 {long_content}"

            result = parse_output_summary(summary_text)

            # 実際には100文字制限を超えていないので認識される
            expected_content = long_content
            assert result["患者情報"] == expected_content

    def test_parse_output_summary_section_aliases_all(self):
        """すべてのセクションエイリアスのテスト"""
        with patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
            "治療経過", "主病名", "症状経過", "現在の処方", "備考"
        ]):
            summary_text = """治療内容
手術を実施

病名
癌

症状
痛み

薬剤
モルヒネ

メモ
注意事項"""

            result = parse_output_summary(summary_text)

            assert result["治療経過"] == "手術を実施"  # 治療内容 → 治療経過
            assert result["主病名"] == "癌"  # 病名 → 主病名
            assert result["症状経過"] == "痛み"  # 症状 → 症状経過
            assert result["現在の処方"] == "モルヒネ"  # 薬剤 → 現在の処方
            assert result["備考"] == "注意事項"  # メモ → 備考

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名"
    ])
    def test_parse_output_summary_whitespace_handling(self):
        """前後の空白文字処理のテスト"""
        summary_text = """  患者情報  
  田中四郎 60歳 男性  

   主病名   
   脳梗塞   """

        result = parse_output_summary(summary_text)

        assert result["患者情報"] == "田中四郎 60歳 男性"
        assert result["主病名"] == "脳梗塞"

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', ["テストセクション"])
    def test_parse_output_summary_empty_input(self):
        """空の入力のテスト"""
        result = parse_output_summary("")
        assert result["テストセクション"] == ""

        result = parse_output_summary("   ")
        assert result["テストセクション"] == ""

        result = parse_output_summary("\n\n\n")
        assert result["テストセクション"] == ""

    def test_format_output_summary_asterisk_removal(self):
        """アスタリスク除去のテスト"""
        test_cases = [
            ("*患者情報*", "患者情報"),
            ("＊主病名＊", "主病名"),
            ("*症状*経過", "症状経過"),
            ("治療＊経過", "治療経過"),
            ("**重要**", "重要"),
            ("＊＊注意＊＊", "注意"),
            ("*", ""),
            ("＊", ""),
            ("通常のテキスト", "通常のテキスト"),
            ("", ""),
        ]

        for input_text, expected in test_cases:
            result = format_output_summary(input_text)
            assert result == expected, f"Input: '{input_text}' Expected: '{expected}' Got: '{result}'"

    def test_format_output_summary_mixed_content(self):
        """混合コンテンツの整形テスト"""
        summary_text = """*患者情報*
田中太郎 ＊75歳＊ 男性

**主病名**
急性心筋梗塞

*治療経過*
緊急手術を実施した。
＊経過良好＊"""

        expected = """患者情報
田中太郎 75歳 男性

主病名
急性心筋梗塞

治療経過
緊急手術を実施した。
経過良好"""

        result = format_output_summary(summary_text)
        assert result == expected

    def test_section_aliases_mapping(self):
        """セクションエイリアスマッピングの確認テスト"""
        expected_aliases = {
            "治療内容": "治療経過",
            "病名": "主病名",
            "症状": "症状経過",
            "処方": "現在の処方",
            "薬剤": "現在の処方",
            "その他": "備考",
            "補足": "備考",
            "メモ": "備考",
        }

        assert section_aliases == expected_aliases

    @patch('utils.text_processor.DEFAULT_SECTION_NAMES', [
        "患者情報", "主病名", "症状経過", "治療経過", "現在の処方", "備考"
    ])
    def test_parse_output_summary_japanese_medical_terminology(self):
        """日本語医療用語の解析テスト"""
        summary_text = """患者情報
鈴木太郎 85歳 男性

主病名
慢性心不全（NYHA分類 III度）

症状経過
労作時呼吸困難が増悪。
浮腫の出現あり。BNP上昇。

治療経過
利尿剤投与開始。
ACE阻害剤を増量。
心臓リハビリテーション導入。

現在の処方
フロセミド 40mg 1日1回朝食後
エナラプリル 5mg 1日2回朝夕食後
カルベジロール 1.25mg 1日2回朝夕食後

備考
外来にて経過観察予定。
体重管理指導実施済み。"""

        result = parse_output_summary(summary_text)

        assert "鈴木太郎 85歳 男性" in result["患者情報"]
        assert "慢性心不全（NYHA分類 III度）" in result["主病名"]
        assert "労作時呼吸困難" in result["症状経過"]
        assert "BNP上昇" in result["症状経過"]
        assert "利尿剤投与開始" in result["治療経過"]
        assert "心臓リハビリテーション導入" in result["治療経過"]
        assert "フロセミド" in result["現在の処方"]
        assert "エナラプリル" in result["現在の処方"]
        assert "カルベジロール" in result["現在の処方"]
        assert "外来にて経過観察予定" in result["備考"]
        assert "体重管理指導実施済み" in result["備考"]