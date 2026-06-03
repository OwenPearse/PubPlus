import unittest

from config.env import parse_database_url


class ParseDatabaseUrlTests(unittest.TestCase):
    def test_standard_supabase_pooler_url(self):
        url = (
            "postgresql://postgres.abcdefgh:secret@aws-1-ap-southeast-2.pooler"
            ".supabase.com:5432/postgres"
        )
        cfg = parse_database_url(url)
        self.assertEqual(cfg["USER"], "postgres.abcdefgh")
        self.assertEqual(cfg["PASSWORD"], "secret")
        self.assertEqual(cfg["HOST"], "aws-1-ap-southeast-2.pooler.supabase.com")
        self.assertEqual(cfg["PORT"], 5432)
        self.assertEqual(cfg["NAME"], "postgres")

    def test_password_with_colon(self):
        url = (
            "postgresql://postgres.ref:part1:fq9HT5Xz_4-Zj@aws.pooler.supabase.com"
            ":5432/postgres"
        )
        cfg = parse_database_url(url)
        self.assertEqual(cfg["PASSWORD"], "part1:fq9HT5Xz_4-Zj")
        self.assertEqual(cfg["PORT"], 5432)

    def test_password_with_at_sign(self):
        url = (
            "postgresql://postgres.ref:xxx@yyy:fq9HT5Xz_4-Zj@aws.pooler.supabase.com"
            ":5432/postgres"
        )
        cfg = parse_database_url(url)
        self.assertEqual(cfg["PASSWORD"], "xxx@yyy:fq9HT5Xz_4-Zj")
        self.assertEqual(cfg["HOST"], "aws.pooler.supabase.com")
        self.assertEqual(cfg["PORT"], 5432)

    def test_percent_encoded_password(self):
        url = "postgresql://user:p%40ss%3Aword@host.example.com:5433/mydb"
        cfg = parse_database_url(url)
        self.assertEqual(cfg["PASSWORD"], "p@ss:word")
        self.assertEqual(cfg["PORT"], 5433)

    def test_sslmode_query_param(self):
        url = "postgresql://u:p@host.example.com:5432/postgres?sslmode=require"
        cfg = parse_database_url(url)
        self.assertEqual(cfg["OPTIONS"], {"sslmode": "require"})

    def test_non_numeric_port_raises(self):
        with self.assertRaises(ValueError):
            parse_database_url(
                "postgresql://postgres.ref:xxx@yyy:fq9HT5Xz_4-Zj/postgres"
            )
