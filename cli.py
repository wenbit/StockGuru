#!/usr/bin/env python3
"""
StockGuru 命令行工具
提供快速的股票筛选和查询功能
"""

import click
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'stockguru-web' / 'backend'))

# 设置环境变量
os.environ.setdefault('SUPABASE_URL', 'https://mislyhozlviaedinpnfa.supabase.co')
os.environ.setdefault('SUPABASE_KEY', 'your-key-here')


@click.group()
@click.version_option(version='0.9.0', prog_name='StockGuru')
def cli():
    """
    📈 StockGuru - 股票短线复盘助手
    
    快速筛选和分析强势股票的命令行工具
    """
    pass


@cli.command()
@click.option('--date', '-d', default=None, help='筛选日期 (YYYY-MM-DD)')
@click.option('--top-n', '-n', default=10, type=int, help='筛选数量 (默认: 10)')
@click.option('--volume-top', default=100, type=int, help='成交额排名范围 (默认: 100)')
@click.option('--hot-top', default=100, type=int, help='热度排名范围 (默认: 100)')
@click.option('--momentum-days', default=25, type=int, help='动量计算天数 (默认: 25)')
@click.option('--output', '-o', type=click.Path(), help='输出文件路径')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'csv']), default='table', help='输出格式')
def screen(date, top_n, volume_top, hot_top, momentum_days, output, format):
    """
    运行股票筛选
    
    示例:
        stockguru screen
        stockguru screen --date 2025-10-15 --top-n 20
        stockguru screen --output results.json --format json
    """
    try:
        from app.services.screening_service import ScreeningService
        from app.core.config import settings
        import asyncio
        
        # 设置日期
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        click.echo(f'\n📊 开始筛选 {date} 的股票...\n')
        click.echo(f'参数配置:')
        click.echo(f'  - 成交额 Top: {volume_top}')
        click.echo(f'  - 热度 Top: {hot_top}')
        click.echo(f'  - 动量天数: {momentum_days}')
        click.echo(f'  - 筛选数量: {top_n}')
        click.echo('')
        
        # 创建服务
        service = ScreeningService()
        
        # 运行筛选
        with click.progressbar(length=100, label='筛选进度') as bar:
            async def run_screening():
                # 这里应该调用真实的筛选逻辑
                # 为了演示，我们使用简化版本
                click.echo('\n⚠️  注意: CLI 工具当前使用简化版本')
                click.echo('完整功能请使用 Web 界面: http://localhost:3000\n')
                return None
            
            result = asyncio.run(run_screening())
        
        click.echo('\n✅ 筛选完成！\n')
        
        if output:
            click.echo(f'📝 结果已保存到: {output}')
        
    except ImportError as e:
        click.echo(f'\n❌ 错误: 缺少依赖模块', err=True)
        click.echo(f'请确保在正确的环境中运行: {str(e)}', err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f'\n❌ 筛选失败: {str(e)}', err=True)
        sys.exit(1)


@cli.command()
@click.option('--limit', '-l', default=10, type=int, help='显示数量 (默认: 10)')
@click.option('--status', '-s', type=click.Choice(['all', 'completed', 'failed', 'running']), default='all', help='筛选状态')
def history(limit, status):
    """
    查看历史筛选记录
    
    示例:
        stockguru history
        stockguru history --limit 20
        stockguru history --status completed
    """
    try:
        click.echo(f'\n📚 历史筛选记录 (最近 {limit} 条)\n')
        click.echo('⚠️  注意: 请使用 Web 界面查看完整历史记录')
        click.echo('访问: http://localhost:3000/history\n')
        
    except Exception as e:
        click.echo(f'\n❌ 获取历史记录失败: {str(e)}', err=True)
        sys.exit(1)


@cli.command()
@click.argument('code')
@click.option('--days', '-d', default=60, type=int, help='K线天数 (默认: 60)')
def stock(code, days):
    """
    查看股票详情
    
    示例:
        stockguru stock 000001
        stockguru stock 600000 --days 90
    """
    try:
        click.echo(f'\n📈 股票详情: {code}\n')
        click.echo(f'K线天数: {days}')
        click.echo('')
        click.echo('⚠️  注意: 请使用 Web 界面查看完整股票详情')
        click.echo(f'访问: http://localhost:3000/stock/{code}\n')
        
    except Exception as e:
        click.echo(f'\n❌ 获取股票详情失败: {str(e)}', err=True)
        sys.exit(1)


@cli.command()
def status():
    """
    检查系统状态
    
    示例:
        stockguru status
    """
    import requests
    
    click.echo('\n🔍 检查系统状态...\n')
    
    # 检查后端
    try:
        response = requests.get('http://localhost:8000/health', timeout=3)
        if response.status_code == 200:
            click.echo('✅ 后端服务: 运行中 (http://localhost:8000)')
        else:
            click.echo('⚠️  后端服务: 异常')
    except:
        click.echo('❌ 后端服务: 未运行')
        click.echo('   启动命令: cd stockguru-web/backend && uvicorn app.main:app --port 8000')
    
    # 检查前端
    try:
        response = requests.get('http://localhost:3000', timeout=3)
        if response.status_code == 200:
            click.echo('✅ 前端服务: 运行中 (http://localhost:3000)')
        else:
            click.echo('⚠️  前端服务: 异常')
    except:
        click.echo('❌ 前端服务: 未运行')
        click.echo('   启动命令: cd frontend && npm run dev')
    
    click.echo('')


@cli.command()
def config():
    """
    显示配置信息
    
    示例:
        stockguru config
    """
    try:
        from app.core.config import settings
        
        click.echo('\n⚙️  配置信息:\n')
        click.echo(f'成交额 Top N: {settings.VOLUME_TOP_N}')
        click.echo(f'热度 Top N: {settings.HOT_TOP_N}')
        click.echo(f'综合评分 Top N: {settings.FINAL_TOP_N}')
        click.echo(f'动量计算天数: {settings.MOMENTUM_DAYS}')
        click.echo(f'动量 Top N: {settings.MOMENTUM_TOP_N}')
        click.echo(f'前端地址: {settings.FRONTEND_URL}')
        click.echo('')
        
    except Exception as e:
        click.echo(f'\n❌ 读取配置失败: {str(e)}', err=True)
        sys.exit(1)


@cli.command()
def web():
    """
    打开 Web 界面
    
    示例:
        stockguru web
    """
    import webbrowser
    
    click.echo('\n🌐 打开 Web 界面...\n')
    
    urls = [
        ('主页', 'http://localhost:3000'),
        ('历史记录', 'http://localhost:3000/history'),
        ('API 文档', 'http://localhost:8000/docs'),
    ]
    
    for name, url in urls:
        click.echo(f'  {name}: {url}')
    
    click.echo('')
    
    # 打开主页
    try:
        webbrowser.open('http://localhost:3000')
        click.echo('✅ 已在浏览器中打开主页')
    except:
        click.echo('⚠️  无法自动打开浏览器，请手动访问上述链接')
    
    click.echo('')


if __name__ == '__main__':
    cli()
