import React from "react"
import { EditorContent, useEditor } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"

interface Props {
  value: string
  onChange: (value: string) => void
  setEditor?: (editor: any) => void
}

const TiptapEditor: React.FC<Props> = ({ value, onChange, setEditor }) => {
  const editor = useEditor({
    extensions: [StarterKit],
    content: value,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
  })
  React.useEffect(() => {
    if (editor) setEditor?.(editor)
  }, [editor, setEditor])
  React.useEffect(() => {
    if (editor && value !== editor.getHTML()) {
      editor.commands.setContent(value)
    }
    // eslint-disable-next-line
  }, [value])
  return <EditorContent editor={editor} />
}

export default TiptapEditor
