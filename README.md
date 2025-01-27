# llm.nvim

A llm neovim plugin for llm compatiable with openai python sdk.

## Requirements

- `python`
```
pip install pyyaml openai
```

## Usage

```vimscript
command! -nargs=* LLM call LLM#RunLLM(<q-args>)
vnoremap <leader>? :<C-u>call LLM#SendSelectionAsPrompt()<CR>
xnoremap <leader>? :<C-u>call LLM#SendSelectionAsPrompt()<CR>
```
