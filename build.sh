#!/bin/bash

# ReplicOOP Build Script
# Compila o projeto Rust e realiza verificações

set -e

echo "🚀 ReplicOOP - Build Script"
echo "============================"
echo ""

# Função para mostrar uso
show_usage() {
    echo "Uso: ./build.sh [OPÇÃO]"
    echo ""
    echo "Opções:"
    echo "  build      - Compila o projeto em modo debug"
    echo "  release    - Compila o projeto em modo release (otimizado)"
    echo "  test       - Executa os testes"
    echo "  fmt        - Formata o código"
    echo "  clippy     - Executa o linter clippy"
    echo "  check      - Verifica o código sem compilar"
    echo "  clean      - Remove arquivos de build"
    echo "  run        - Compila e executa"
    echo "  install    - Instala o binário no sistema"
    echo "  all        - Executa fmt, clippy, test e build release"
    echo ""
}

# Verifica se Rust está instalado
check_rust() {
    if ! command -v cargo &> /dev/null; then
        echo "❌ Rust não encontrado!"
        echo "💡 Instale Rust em: https://rustup.rs/"
        exit 1
    fi
    echo "✅ Rust instalado: $(rustc --version)"
    echo ""
}

# Build debug
build_debug() {
    echo "🔨 Compilando em modo debug..."
    cargo build
    echo "✅ Build debug concluído!"
    echo "📦 Binário: target/debug/replicoop"
}

# Build release
build_release() {
    echo "🔨 Compilando em modo release (otimizado)..."
    cargo build --release
    echo "✅ Build release concluído!"
    echo "📦 Binário: target/release/replicoop"
    echo "💡 Copie este binário para produção"
}

# Testes
run_tests() {
    echo "🧪 Executando testes..."
    cargo test
    echo "✅ Testes concluídos!"
}

# Formatação
run_fmt() {
    echo "🎨 Formatando código..."
    cargo fmt
    echo "✅ Código formatado!"
}

# Clippy
run_clippy() {
    echo "🔍 Executando clippy (linter)..."
    cargo clippy -- -D warnings
    echo "✅ Clippy passou!"
}

# Check
run_check() {
    echo "🔍 Verificando código..."
    cargo check
    echo "✅ Verificação concluída!"
}

# Clean
run_clean() {
    echo "🧹 Limpando arquivos de build..."
    cargo clean
    echo "✅ Limpeza concluída!"
}

# Run
run_app() {
    echo "🚀 Compilando e executando..."
    cargo run
}

# Install
run_install() {
    echo "📦 Instalando binário no sistema..."
    cargo install --path .
    echo "✅ Instalado com sucesso!"
    echo "💡 Agora você pode usar: replicoop"
}

# All
run_all() {
    run_fmt
    echo ""
    run_clippy
    echo ""
    run_tests
    echo ""
    build_release
    echo ""
    echo "🎉 Tudo pronto!"
}

# Verificar Rust
check_rust

# Processar argumentos
case "${1:-}" in
    build)
        build_debug
        ;;
    release)
        build_release
        ;;
    test)
        run_tests
        ;;
    fmt)
        run_fmt
        ;;
    clippy)
        run_clippy
        ;;
    check)
        run_check
        ;;
    clean)
        run_clean
        ;;
    run)
        run_app
        ;;
    install)
        run_install
        ;;
    all)
        run_all
        ;;
    -h|--help|help)
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        echo "❌ Opção inválida: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
