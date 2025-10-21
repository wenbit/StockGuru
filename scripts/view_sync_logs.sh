#!/bin/bash
#
# 数据同步日志查看工具
# 使用方法: ./scripts/view_sync_logs.sh [选项]
#

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 日志文件路径
LOG_FILE="logs/backend.log"

# 显示帮助信息
show_help() {
    echo "数据同步日志查看工具"
    echo ""
    echo "使用方法:"
    echo "  $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -f, --follow      实时跟踪日志（默认）"
    echo "  -l, --last N      查看最近 N 行日志（默认 50）"
    echo "  -p, --progress    只显示进度信息"
    echo "  -a, --all         显示所有同步相关日志"
    echo "  -s, --status      显示当前同步状态"
    echo "  -h, --help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                # 实时跟踪进度日志"
    echo "  $0 -l 100         # 查看最近 100 行"
    echo "  $0 -a             # 实时跟踪所有同步日志"
    echo "  $0 -s             # 查看当前状态"
    echo ""
}

# 检查日志文件是否存在
check_log_file() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${RED}错误：日志文件不存在 ($LOG_FILE)${NC}"
        echo "请确保后端服务正在运行"
        exit 1
    fi
}

# 显示当前同步状态
show_status() {
    check_log_file
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}当前同步状态${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # 获取最新的进度信息
    latest_progress=$(tail -100 "$LOG_FILE" | grep "test_copy_sync: 进度" | tail -1)
    
    if [ -n "$latest_progress" ]; then
        echo -e "${YELLOW}最新进度：${NC}"
        echo "$latest_progress"
        echo ""
        
        # 提取关键信息
        if [[ $latest_progress =~ 进度:\ ([0-9]+)/([0-9]+)\ \(([0-9]+)%\) ]]; then
            current="${BASH_REMATCH[1]}"
            total="${BASH_REMATCH[2]}"
            percent="${BASH_REMATCH[3]}"
            
            echo -e "  📊 进度: ${GREEN}${current}${NC}/${total} (${GREEN}${percent}%${NC})"
        fi
        
        if [[ $latest_progress =~ 成功:\ ([0-9]+) ]]; then
            success="${BASH_REMATCH[1]}"
            echo -e "  ✅ 成功: ${GREEN}${success}${NC}"
        fi
        
        if [[ $latest_progress =~ 失败:\ ([0-9]+) ]]; then
            failed="${BASH_REMATCH[1]}"
            if [ "$failed" -eq 0 ]; then
                echo -e "  ❌ 失败: ${GREEN}${failed}${NC}"
            else
                echo -e "  ❌ 失败: ${RED}${failed}${NC}"
            fi
        fi
        
        if [[ $latest_progress =~ 速度:\ ([0-9.]+)股/秒 ]]; then
            speed="${BASH_REMATCH[1]}"
            echo -e "  🚀 速度: ${BLUE}${speed}${NC} 股/秒"
        fi
        
        if [[ $latest_progress =~ 预计剩余:\ ([0-9]+)秒 ]]; then
            eta="${BASH_REMATCH[1]}"
            eta_min=$((eta / 60))
            echo -e "  ⏳ 预计剩余: ${YELLOW}${eta_min}${NC} 分钟"
        fi
    else
        echo -e "${YELLOW}没有找到同步进度信息${NC}"
        echo "可能同步任务尚未开始或已完成"
    fi
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 实时跟踪进度日志
follow_progress() {
    check_log_file
    
    echo -e "${GREEN}📋 实时跟踪同步进度${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止${NC}"
    echo ""
    
    # 先显示最近的几条
    echo -e "${BLUE}最近进度：${NC}"
    tail -20 "$LOG_FILE" | grep "test_copy_sync: 进度" | tail -5
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}实时日志：${NC}"
    echo ""
    
    # 实时跟踪
    tail -f "$LOG_FILE" | grep --line-buffered "test_copy_sync: 进度"
}

# 实时跟踪所有同步日志
follow_all() {
    check_log_file
    
    echo -e "${GREEN}📋 实时跟踪所有同步日志${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止${NC}"
    echo ""
    
    # 先显示最近的几条
    echo -e "${BLUE}最近日志：${NC}"
    tail -20 "$LOG_FILE" | grep "test_copy_sync" | tail -10
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}实时日志：${NC}"
    echo ""
    
    # 实时跟踪
    tail -f "$LOG_FILE" | grep --line-buffered "test_copy_sync"
}

# 查看最近的日志
show_last() {
    local lines=${1:-50}
    check_log_file
    
    echo -e "${GREEN}📋 最近 ${lines} 行同步日志${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    tail -"$lines" "$LOG_FILE" | grep "test_copy_sync"
}

# 主程序
main() {
    # 默认选项
    action="follow_progress"
    lines=50
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--follow)
                action="follow_progress"
                shift
                ;;
            -a|--all)
                action="follow_all"
                shift
                ;;
            -l|--last)
                action="show_last"
                lines="${2:-50}"
                shift 2
                ;;
            -p|--progress)
                action="follow_progress"
                shift
                ;;
            -s|--status)
                action="show_status"
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}未知选项: $1${NC}"
                echo "使用 -h 或 --help 查看帮助"
                exit 1
                ;;
        esac
    done
    
    # 执行对应的操作
    case $action in
        follow_progress)
            follow_progress
            ;;
        follow_all)
            follow_all
            ;;
        show_last)
            show_last "$lines"
            ;;
        show_status)
            show_status
            ;;
    esac
}

# 运行主程序
main "$@"
