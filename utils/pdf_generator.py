"""
PDF 생성 유틸리티 - Enhanced Version
Markdown 형식의 리포트를 전문적인 PDF로 변환합니다.
"""
import os
from datetime import datetime
from typing import Optional, List
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, ListFlowable, ListItem, KeepTogether, HRFlowable
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re


class PDFGenerator:
    """Markdown을 PDF로 변환하는 클래스"""
    
    def __init__(self, output_dir: str = "outputs/reports"):
        self.output_dir = output_dir
        self.korean_font = self.setup_fonts()
        
        # 색상 테마 정의
        self.colors = {
            'primary': colors.HexColor('#2C3E50'),
            'secondary': colors.HexColor('#3498DB'),
            'accent': colors.HexColor('#E74C3C'),
            'success': colors.HexColor('#27AE60'),
            'text': colors.HexColor('#2C3E50'),
            'light_gray': colors.HexColor('#ECF0F1'),
            'dark_gray': colors.HexColor('#7F8C8D'),
            'table_header': colors.HexColor('#34495E'),
            'table_alt_row': colors.HexColor('#F8F9FA')
        }
        
    def setup_fonts(self):
        """한글 폰트 설정"""
        
        try:
            # Windows 시스템 폰트 경로
            font_paths = [
                r"C:\Windows\Fonts\malgun.ttf",      # 맑은 고딕
                r"C:\Windows\Fonts\gulim.ttc",        # 굴림
                r"C:\Windows\Fonts\batang.ttc",       # 바탕
                r"C:\Windows\Fonts\NanumGothic.ttf",  # 나눔고딕
            ]
            
            # 사용 가능한 폰트 찾기
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('KoreanFont', font_path))
                        print(f"   한글 폰트 등록 성공: {font_path}")
                        return 'KoreanFont'
                    except Exception as e:
                        continue
            
            # 폰트를 찾지 못한 경우 기본 폰트 사용
            print("   경고: 한글 폰트를 찾을 수 없습니다. 기본 폰트 사용")
            return 'Helvetica'
            
        except Exception as e:
            print(f"   경고: 폰트 설정 중 오류: {e}")
            return 'Helvetica'
    
    def markdown_to_pdf(
        self, 
        markdown_text: str, 
        filename: Optional[str] = None,
        title: str = "전기차 시장 트렌드 분석 리포트"
    ) -> str:
        """
        Markdown 텍스트를 PDF로 변환
        
        Args:
            markdown_text: Markdown 형식의 텍스트
            filename: 출력 파일명 (None이면 자동 생성)
            title: 문서 제목
        
        Returns:
            생성된 PDF 파일 경로
        """
        # 파일명 생성
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ev_market_analysis_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # PDF 문서 생성
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        
        # 스타일 설정
        styles = self._create_styles()
        
        # 컨텐츠 파싱
        story = []
        
        # 제목 추가
        story.append(Paragraph(title, styles['TitleCustom']))
        story.append(Spacer(1, 0.5*cm))
        
        # 생성 날짜
        date_str = datetime.now().strftime("%Y년 %m월 %d일")
        # Normal 스타일에도 한글 폰트 적용
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontName=self.korean_font
        )
        story.append(Paragraph(f"생성일: {date_str}", date_style))
        story.append(Spacer(1, 1*cm))
        
        # Markdown 파싱 및 변환
        story.extend(self._parse_markdown(markdown_text, styles))
        
        # PDF 빌드
        doc.build(story)
        
        print(f"PDF 생성 완료: {filepath}")
        return filepath
    
    def _create_styles(self):
        """PDF 스타일 정의 - Enhanced"""
        styles = getSampleStyleSheet()
        
        # 메인 제목 스타일
        styles.add(ParagraphStyle(
            name='TitleCustom',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.colors['primary'],
            spaceAfter=12,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName=self.korean_font,
            leading=28
        ))
        
        # 부제목 스타일
        styles.add(ParagraphStyle(
            name='SubtitleCustom',
            parent=styles['Normal'],
            fontSize=11,
            textColor=self.colors['dark_gray'],
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName=self.korean_font
        ))
        
        # 대제목 스타일 (# Heading)
        styles.add(ParagraphStyle(
            name='Heading1Custom',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=self.colors['primary'],
            spaceAfter=12,
            spaceBefore=20,
            fontName=self.korean_font,
            leading=22,
            borderWidth=0,
            borderColor=self.colors['secondary'],
            borderPadding=5
        ))
        
        # 중제목 스타일 (## Heading)
        styles.add(ParagraphStyle(
            name='Heading2Custom',
            parent=styles['Heading2'],
            fontSize=15,
            textColor=self.colors['secondary'],
            spaceAfter=10,
            spaceBefore=15,
            fontName=self.korean_font,
            leading=18
        ))
        
        # 소제목 스타일 (### Heading)
        styles.add(ParagraphStyle(
            name='Heading3Custom',
            parent=styles['Heading3'],
            fontSize=13,
            textColor=self.colors['dark_gray'],
            spaceAfter=8,
            spaceBefore=12,
            fontName=self.korean_font,
            leading=16
        ))
        
        # 본문 스타일
        styles.add(ParagraphStyle(
            name='BodyCustom',
            parent=styles['BodyText'],
            fontSize=10,
            leading=15,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName=self.korean_font,
            textColor=self.colors['text']
        ))
        
        # 리스트 스타일
        styles.add(ParagraphStyle(
            name='BulletCustom',
            parent=styles['BodyText'],
            fontSize=10,
            leading=15,
            leftIndent=20,
            spaceAfter=5,
            fontName=self.korean_font,
            textColor=self.colors['text']
        ))
        
        # 테이블 셀 스타일
        styles.add(ParagraphStyle(
            name='TableCell',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            fontName=self.korean_font,
            textColor=self.colors['text']
        ))
        
        # 테이블 헤더 스타일
        styles.add(ParagraphStyle(
            name='TableHeader',
            parent=styles['Normal'],
            fontSize=10,
            leading=13,
            fontName=self.korean_font,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
        
        return styles
    
    def _parse_markdown(self, markdown_text: str, styles) -> list:
        """Markdown 텍스트를 PDF 요소로 파싱 - 테이블 지원 추가"""
        story = []
        lines = markdown_text.split('\n')
        
        in_list = False
        list_items = []
        in_table = False
        table_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # 테이블 감지 (| ... | 형식)
            if line.strip().startswith('|') and '|' in line[1:]:
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(line)
                i += 1
                continue
            elif in_table and not line.strip().startswith('|'):
                # 테이블 종료
                if table_lines:
                    table = self._create_table_from_markdown(table_lines, styles)
                    if table:
                        story.append(Spacer(1, 0.3*cm))
                        story.append(table)
                        story.append(Spacer(1, 0.3*cm))
                table_lines = []
                in_table = False
            
            # 빈 줄
            if not line.strip():
                if in_list:
                    story.extend(list_items)
                    list_items = []
                    in_list = False
                story.append(Spacer(1, 0.2*cm))
                i += 1
                continue
            
            # 구분선 (---)
            if line.strip().startswith('---'):
                if in_list:
                    story.extend(list_items)
                    list_items = []
                    in_list = False
                story.append(HRFlowable(width="100%", thickness=1, color=self.colors['light_gray'], spaceAfter=0.3*cm, spaceBefore=0.3*cm))
                i += 1
                continue
            
            # Heading 1 (#)
            if line.strip().startswith('# ') and not line.strip().startswith('##'):
                if in_list:
                    story.extend(list_items)
                    list_items = []
                    in_list = False
                text = line.strip()[2:].strip()
                story.append(Paragraph(text, styles['Heading1Custom']))
                i += 1
                continue
            
            # Heading 2 (##)
            if line.strip().startswith('## ') and not line.strip().startswith('###'):
                if in_list:
                    story.extend(list_items)
                    list_items = []
                    in_list = False
                text = line.strip()[3:].strip()
                story.append(Paragraph(text, styles['Heading2Custom']))
                i += 1
                continue
            
            # Heading 3 (###)
            if line.strip().startswith('### '):
                if in_list:
                    story.extend(list_items)
                    list_items = []
                    in_list = False
                text = line.strip()[4:].strip()
                story.append(Paragraph(text, styles['Heading3Custom']))
                i += 1
                continue
            
            # 리스트 항목 (- 또는 *)
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                text = line.strip()[2:].strip()
                text = self._process_inline_markdown(text)
                list_items.append(Paragraph(f"• {text}", styles['BulletCustom']))
                in_list = True
                i += 1
                continue
            
            # 숫자 리스트 (1. 2. 3.)
            if re.match(r'^\d+\.\s', line.strip()):
                text = re.sub(r'^\d+\.\s', '', line.strip()).strip()
                text = self._process_inline_markdown(text)
                list_items.append(Paragraph(f"• {text}", styles['BulletCustom']))
                in_list = True
                i += 1
                continue
            
            # 일반 텍스트
            if in_list:
                story.extend(list_items)
                list_items = []
                in_list = False
            
            if line.strip():
                text = self._process_inline_markdown(line.strip())
                story.append(Paragraph(text, styles['BodyCustom']))
            
            i += 1
        
        # 마지막 리스트 처리
        if in_list and list_items:
            story.extend(list_items)
        
        # 마지막 테이블 처리
        if in_table and table_lines:
            table = self._create_table_from_markdown(table_lines, styles)
            if table:
                story.append(Spacer(1, 0.3*cm))
                story.append(table)
                story.append(Spacer(1, 0.3*cm))
        
        return story
    
    def _create_table_from_markdown(self, table_lines: List[str], styles):
        """Markdown 테이블을 PDF Table로 변환"""
        if len(table_lines) < 2:
            return None
        
        # 테이블 데이터 파싱
        table_data = []
        header_row_idx = None
        
        for i, line in enumerate(table_lines):
            # | 기준으로 분할
            cells = [cell.strip() for cell in line.split('|')]
            # 첫 번째와 마지막 빈 셀 제거
            cells = [cell for cell in cells if cell]
            
            if not cells:
                continue
            
            # 구분선 (|---|---|) 감지 - 헤더와 데이터 구분
            if all(set(cell.strip()).issubset({'-', ':', ' '}) for cell in cells):
                header_row_idx = i
                continue
            
            # 셀 데이터를 Paragraph로 변환
            if header_row_idx is None or i < header_row_idx:
                # 헤더 행
                styled_cells = [Paragraph(self._process_inline_markdown(cell), styles['TableHeader']) for cell in cells]
            else:
                # 데이터 행
                styled_cells = [Paragraph(self._process_inline_markdown(cell), styles['TableCell']) for cell in cells]
            
            table_data.append(styled_cells)
        
        if not table_data:
            return None
        
        # 테이블 생성
        # 열 너비 자동 조정
        col_count = len(table_data[0])
        available_width = 17*cm  # A4 용지의 사용 가능한 너비
        col_widths = [available_width / col_count] * col_count
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # 테이블 스타일 정의
        table_style = [
            # 헤더 스타일
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['table_header']),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.korean_font),
            
            # 테두리
            ('GRID', (0, 0), (-1, -1), 0.5, self.colors['dark_gray']),
            ('BOX', (0, 0), (-1, -1), 1, self.colors['primary']),
            
            # 패딩
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]
        
        # 교차 행 배경색 (zebra striping)
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), self.colors['table_alt_row']))
        
        table.setStyle(TableStyle(table_style))
        
        return table
    
    def _process_inline_markdown(self, text: str) -> str:
        """인라인 마크다운 처리 (bold, italic 등)"""
        # **bold** -> <b>bold</b>
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        
        # *italic* -> <i>italic</i> (단, **가 아닐 때만)
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)
        
        # `code` -> <font name="Courier">code</font>
        text = re.sub(r'`(.+?)`', r'<font name="Courier">\1</font>', text)
        
        # Emoji 처리 (그대로 유지)
        return text


def create_pdf_generator(output_dir: str = "outputs/reports") -> PDFGenerator:
    """PDFGenerator 생성 팩토리 함수"""
    return PDFGenerator(output_dir)


# 사용 예시
if __name__ == "__main__":
    generator = PDFGenerator()
    
    sample_markdown = """
# 전기차 시장 분석 리포트

## Executive Summary
- 핵심 발견사항 1
- 핵심 발견사항 2
- 핵심 발견사항 3

## 시장 환경 분석

### 소비자 여론
전기차에 대한 소비자 인식이 개선되고 있습니다.

### 시장 현황
**판매량**이 전년 대비 *30% 증가*했습니다.

## 결론
전기차 시장은 지속적으로 성장할 것으로 예상됩니다.
"""
    
    generator.markdown_to_pdf(sample_markdown)

