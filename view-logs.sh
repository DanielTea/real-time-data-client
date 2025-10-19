#!/bin/bash
# Helper script to view Polymarket logs

case "$1" in
  tail)
    # Show last 50 lines
    tail -50 polymarket-logs.txt
    ;;
  follow)
    # Follow logs in real-time (Ctrl+C to stop)
    tail -f polymarket-logs.txt
    ;;
  grep)
    # Search logs for a pattern
    if [ -z "$2" ]; then
      echo "Usage: ./view-logs.sh grep <pattern>"
      exit 1
    fi
    grep "$2" polymarket-logs.txt
    ;;
  deleted)
    # Show only market deletion logs
    grep "Deleted market" polymarket-logs.txt
    ;;
  check)
    # Show only market check cycle logs
    grep "Checking.*markets for closure" polymarket-logs.txt | tail -10
    ;;
  clear)
    # Clear the log file
    > polymarket-logs.txt
    echo "Logs cleared"
    ;;
  *)
    echo "Polymarket Log Viewer"
    echo ""
    echo "Usage: ./view-logs.sh <command>"
    echo ""
    echo "Commands:"
    echo "  tail      Show last 50 lines of logs"
    echo "  follow    Follow logs in real-time (Ctrl+C to stop)"
    echo "  grep      Search logs for a pattern"
    echo "  deleted   Show only market deletion logs"
    echo "  check     Show last 10 market check cycles"
    echo "  clear     Clear the log file"
    echo ""
    echo "Examples:"
    echo "  ./view-logs.sh tail"
    echo "  ./view-logs.sh follow"
    echo "  ./view-logs.sh grep 'Bitcoin'"
    echo "  ./view-logs.sh deleted"
    ;;
esac

