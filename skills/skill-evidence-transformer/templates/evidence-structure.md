# Evidence Structure

## Proof Tag (Single Line)

```markdown
<proof file="file.md" lines="8-12" preview="Use camelCase for..." />
```

- **Single line only**
- `preview`: First 20-30 chars of the quote, ending with `...`
- Purpose: Verify document was read, not reproduce content

## Example

After reading:
```markdown
<action tool="read_file">
knowledge/rules.md
</action>

<proof file="rules.md" lines="5-9" preview="Functions should use..." />
```

## Multiple Documents

```markdown
<proof file="file1.md" lines="3-7" preview="The config requires..." />
<proof file="file2.md" lines="12" preview="Default timeout is..." />
```

## Output

```markdown
<final>
[Answer based on proofs]
</final>
```

## Failure

```markdown
<proof file="file.md" lines="?" preview="FAILED" />
<final>Error: Could not load file.</final>
```
