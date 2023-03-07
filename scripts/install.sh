for dir in packages/*; do
    if [ $dir = "packages/jupyter-ai-module-cookiecutter" ]; then
        echo "skipped"
        continue
    fi

    echo "Installing $dir in editable mode..."
    (cd "$dir" && pip install -e ".[test]") || exit 1
done
