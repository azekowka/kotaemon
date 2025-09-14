'use client';

import { useState, useEffect, useRef } from 'react';
import { sendMessage, getChatSuggestions, uploadFile, getFiles } from '../lib/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { ScrollArea } from '../components/ui/scroll-area';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';

interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
}

interface FileInfo {
  id: string;
  name: string;
}

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [conversationId, setConversationId] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<FileInfo[]>([]);
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchChatSuggestions();
    fetchFiles();
  }, []);

  const fetchChatSuggestions = async () => {
    try {
      const newSuggestions = await getChatSuggestions();
      setSuggestions(newSuggestions);
    } catch (error) {
      console.error("Error fetching chat suggestions:", error);
    }
  };

  const fetchFiles = async () => {
    try {
      const files = await getFiles();
      setUploadedFiles(files);
    } catch (error) {
      console.error("Error fetching files:", error);
    }
  };

  const handleSendMessage = async () => {
    if (input.trim() === '' || loading) return;

    const userMessage: ChatMessage = { sender: 'user', text: input };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const history = messages.map((msg) => [msg.text, msg.text]);
      const responseBody = await sendMessage(input, history, conversationId, selectedFileIds);
      const reader = responseBody?.getReader();
      const decoder = new TextDecoder();

      let botResponseText = '';
      setMessages((prevMessages) => [...prevMessages, { sender: 'bot', text: '' }]);

      while (true) {
        const { value, done } = await reader!.read();
        if (done) break;
        const chunk = decoder.decode(value);
        botResponseText += chunk;
        setMessages((prevMessages) => {
          const newMessages = [...prevMessages];
          newMessages[newMessages.length - 1] = { sender: 'bot', text: botResponseText };
          return newMessages;
        });
      }
      // Update conversation ID if the backend sends it back (not implemented yet in backend)
      // setConversationId(newConversationId);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'bot', text: "Error: Could not get a response." },
      ]);
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files) return;

    const file = event.target.files[0];
    if (file) {
      try {
        setLoading(true);
        const result = await uploadFile(file);
        console.log("File upload result:", result);
        fetchFiles(); // Refresh the list of uploaded files
      } catch (error) {
        console.error("Error uploading file:", error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleFileSelection = (fileId: string) => {
    setSelectedFileIds((prev) =>
      prev.includes(fileId) ? prev.filter((id) => id !== fileId) : [...prev, fileId]
    );
  };

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <header className="border-b px-4 py-2 flex items-center justify-between">
        <h1 className="text-xl font-bold">Kotaemon Chat</h1>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Panel: Suggestions and Files */}
        <aside className="w-72 border-r p-4 flex flex-col">
          <Card className="mb-4 flex-1 flex flex-col">
            <CardHeader>
              <CardTitle>Suggestions</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-auto">
              <ScrollArea className="h-full pr-2">
                <div className="space-y-2">
                  {suggestions.map((suggestion, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      className="w-full justify-start text-left"
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          <Card className="flex-1 flex flex-col">
            <CardHeader>
              <CardTitle>Files</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-auto">
              <ScrollArea className="h-full pr-2">
                <div className="space-y-2">
                  {uploadedFiles.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-2 rounded-md hover:bg-muted/50"
                    >
                      <Label htmlFor={`file-${file.id}`} className="flex-1 cursor-pointer">
                        {file.name}
                      </Label>
                      <Checkbox
                        id={`file-${file.id}`}
                        checked={selectedFileIds.includes(file.id)}
                        onCheckedChange={() => handleFileSelection(file.id)}
                      />
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          <div className="mt-4">
            <input
              type="file"
              ref={fileInputRef}
              className="hidden"
              onChange={handleFileUpload}
              accept=".pdf,.txt,.md,.json"
            />
            <Button
              className="w-full"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
            >
              Upload File
            </Button>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="flex-1 flex flex-col p-4 bg-muted/20">
          <ScrollArea className="flex-1 pr-4">
            <div className="space-y-4">
              {messages.length === 0 && !loading ? (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  Start a conversation...
                </div>
              ) : (
                messages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <Card
                      className={`max-w-xs ${msg.sender === 'user' ? 'bg-primary text-primary-foreground' : ''}`}
                    >
                      <CardContent className="p-3">
                        {msg.text}
                      </CardContent>
                    </Card>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
          {loading && (
            <div className="flex justify-center items-center py-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
            </div>
          )}
        </main>
      </div>

      <footer className="border-t px-4 py-2 flex items-center">
        <Input
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleSendMessage();
            }
          }}
          disabled={loading}
          className="flex-1 mr-2"
        />
        <Button onClick={handleSendMessage} disabled={loading}>
          Send
        </Button>
      </footer>
    </div>
  );
}
