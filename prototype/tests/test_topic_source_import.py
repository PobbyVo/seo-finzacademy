"""Run: python -m unittest discover -s tests -p 'test_topic_source_import.py' -v"""
import csv
import io
import sys
import unittest
from pathlib import Path

from openpyxl import Workbook
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from topic_source_import import parse_topic_source

ROOT=Path(__file__).resolve().parents[2]

class TopicSourceImportTest(unittest.TestCase):
    def test_normalized_real_source_fixture(self):
        filename=ROOT/'fixtures'/'FINZ_TOPIC_IMPORT_READY.xlsx'
        data=parse_topic_source(filename.read_bytes(),filename.name)
        self.assertEqual(data['stats']['validTopics'],25)
        self.assertEqual(data['stats']['contentCodes'],63)
        self.assertEqual(data['stats']['keywordRows'],299)
        self.assertEqual(data['detected']['taxonomyHeaderRow'],1)
        self.assertTrue(data['stats']['complete'])
        p01=[g for g in data['contentGroups'] if g['topicCode']=='P01']
        self.assertEqual([(g['primaryCount'],len(g['secondaries'])) for g in p01],[(1,5),(1,5)])
        self.assertEqual(p01[0]['primary'],'lương gross net là gì')
        self.assertEqual(p01[1]['primary'],'cách deal lương')
        self.assertEqual(p01[0]['keywords'][0]['funnelSource'],'TOFU')
        self.assertEqual(p01[0]['keywords'][0]['metricStatus'],'NOT_MEASURED')

    def test_generic_no_hardcoding_and_header_row4(self):
        wb=Workbook();tab=wb.active;tab.title='CHU DE 2026';tab.append(['Title']);tab.append(['instructions']);tab.append(['empty']);tab.append(['Mã','Topic pillar','Pillar','Loại topic','Trục chia của pillar','Chủ đề chính bên trong']);tab.append(['Z42','Thiết bị làm bánh','HÀNG GIA DỤNG','Theo thứ cụ thể','Theo loại thiết bị','Lò nướng · Máy trộn bột'])
        kw=wb.create_sheet('MY-KEYWORD-DATA');kw.append(['Key','Loại','Giai đoạn','Mã nội dung gốc','Chủ đề','Nội dung gốc']);kw.append(['máy trộn bột có tốt không','Chính','TOFU','Z42.1-A','Máy trộn bột','Giải thích và chọn máy trộn bột']);kw.append(['nên mua máy trộn bột loại nào','Phụ','MOFU','Z42.1-A','Máy trộn bột','Giải thích và chọn máy trộn bột']);b=io.BytesIO();wb.save(b)
        data=parse_topic_source(b.getvalue(),'generic.xlsx')
        self.assertEqual(data['stats']['validTopics'],1)
        self.assertEqual(data['detected']['taxonomyHeaderRow'],4)
        self.assertEqual(data['contentGroups'][0]['topicCode'],'Z42')
        self.assertEqual(data['contentGroups'][0]['primary'],'máy trộn bột có tốt không')
        self.assertEqual(data['contentGroups'][0]['secondaries'],['nên mua máy trộn bột loại nào'])

    def test_missing_taxonomy_field_blocks_topic(self):
        wb=Workbook();w=wb.active;w.title='Topic Pillar';w.append(['Mã','Topic pillar','Pillar','Loại topic','Trục chia của pillar','Chủ đề chính bên trong']);w.append(['X01','Tài chính','KIẾM TIỀN','','Nguồn thu','Lương']);k=wb.create_sheet('Keywords');k.append(['Key','Loại','Mã nội dung gốc','Chủ đề','Nội dung gốc']);k.append(['lương là gì','Chính','X01.1','Lương','Định nghĩa lương'])
        b=io.BytesIO();wb.save(b);data=parse_topic_source(b.getvalue(),'missing.xlsx')
        self.assertEqual(data['stats']['validTopics'],0)
        self.assertEqual(data['stats']['incompleteTopics'],1)
        self.assertEqual(data['stats']['orphanKeywords'],1)
        self.assertTrue(any(x['code']=='INCOMPLETE_TOPIC' for x in data['warnings']))

    def test_two_separate_csv_parts(self):
        t='Mã,Topic pillar,Pillar,Loại topic,Trục chia của pillar,Chủ đề chính bên trong\nB10,Đồ gia dụng,MUA SẮM,Theo thứ cụ thể,Theo sản phẩm,Máy hút bụi\n'
        k='Key,Loại,Giai đoạn,Mã nội dung gốc,Chủ đề,Nội dung gốc\nmáy hút bụi tốt,Chính,TOFU,B10.1,Loại máy hút bụi,Chọn máy hút bụi\n'
        a=parse_topic_source(t.encode(),'topic.csv')
        b=parse_topic_source(k.encode(),'keyword.csv')
        self.assertEqual(a['stats']['validTopics'],1)
        self.assertEqual(a['stats']['keywordRows'],0)
        self.assertFalse(a['stats']['complete'])
        self.assertEqual(b['stats']['validTopics'],0)
        self.assertEqual(b['stats']['keywordRows'],1)
        self.assertFalse(b['stats']['complete'])

if __name__=='__main__':unittest.main()
