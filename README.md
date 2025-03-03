# llm.nvim

A llm neovim plugin for llm compatiable with openai python sdk.

## Requirements

- `python`
```
pip install pyyaml openai
```

- If you have `uv` installed, then you do not need install these pacakges manually.

## Usage

```vimscript
command! -nargs=* LLM call LLM#RunLLM(<q-args>)
vnoremap <leader>? :<C-u>call LLM#SendSelectionAsPrompt()<CR>
xnoremap <leader>? :<C-u>call LLM#SendSelectionAsPrompt()<CR>
```
