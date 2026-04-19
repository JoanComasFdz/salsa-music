FROM mcr.microsoft.com/devcontainers/base:jammy

USER root

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      zsh git curl wget gpg ca-certificates zip \
 && mkdir -p /etc/apt/keyrings \
 && wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc \
      | gpg --dearmor -o /etc/apt/keyrings/gierens.gpg \
 && echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" \
      > /etc/apt/sources.list.d/gierens.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends eza \
 && curl -sSfL https://raw.githubusercontent.com/ajeetdsouza/zoxide/main/install.sh \
      | bash -s -- --bin-dir /usr/local/bin \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @anthropic-ai/claude-code \
 && rm -rf /var/lib/apt/lists/* \
 && chsh -s /usr/bin/zsh vscode

USER vscode

RUN rm -rf "$HOME/.oh-my-zsh" \
 && RUNZSH=no KEEP_ZSHRC=yes sh -c \
      "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
      "" --unattended \
 && git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions \
      "$HOME/.oh-my-zsh/custom/plugins/zsh-autosuggestions" \
 && git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting \
      "$HOME/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting" \
 && git clone --depth=1 https://github.com/spaceship-prompt/spaceship-prompt.git \
      "$HOME/.oh-my-zsh/custom/themes/spaceship-prompt" \
 && ln -sf "$HOME/.oh-my-zsh/custom/themes/spaceship-prompt/spaceship.zsh-theme" \
      "$HOME/.oh-my-zsh/custom/themes/spaceship.zsh-theme"

COPY --chown=vscode:vscode .zshrc /home/vscode/.zshrc
