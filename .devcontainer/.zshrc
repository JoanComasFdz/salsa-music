# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"
export PATH="$HOME/.local/bin:$PATH"

# Theme
ZSH_THEME="spaceship"

# Disable auto-setting terminal title
DISABLE_AUTO_TITLE="true"

# Plugins
plugins=(
  git
  zsh-autosuggestions
  zsh-syntax-highlighting
  sudo
  extract
  history
  docker
  npm
)

# Spaceship configuration (BEFORE sourcing oh-my-zsh)
SPACESHIP_USER_SHOW=always
SPACESHIP_CHAR_SYMBOL="❯"
SPACESHIP_CHAR_SUFFIX=" "
SPACESHIP_EXEC_TIME_SHOW=true
SPACESHIP_EXEC_TIME_ELAPSED=1
SPACESHIP_EXEC_TIME_PRECISION=2
SPACESHIP_EXEC_TIME_PREFIX="⏱ "
SPACESHIP_EXEC_TIME_SUFFIX=" "
SPACESHIP_EXEC_TIME_COLOR="yellow"

SPACESHIP_PROMPT_ORDER=(
  user
  dir
  host
  git
  exec_time
  line_sep
  jobs
  exit_code
  char
)

# Source Oh My Zsh (THIS MUST BE AFTER SPACESHIP CONFIG)
source $ZSH/oh-my-zsh.sh

# nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# zoxide (smarter cd)
eval "$(zoxide init zsh)"

# eza alias (modern ls)
alias l='eza --long --all --header --icons --group-directories-first --no-permissions --no-user'

# Editor
export EDITOR="code --wait"

# Tips on startup
echo "Tip: use 'z' instead of 'cd' to change directories!"
echo "Tip: use 'l' instead of 'ls' to explore directories!"
