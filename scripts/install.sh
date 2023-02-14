for dir in packages/* 
    do (cd "$dir" && pip install -e ".[test]") || exit 1
done