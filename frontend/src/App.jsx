import { useState, useRef, useEffect } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [systemPrompt, setSystemPrompt] = useState(
    "You are a helpful AI assistant."
  );
  const [loading, setLoading] = useState(false);

  const sessionId = useRef(crypto.randomUUID());

  useEffect(() => {
    console.log("Session:", sessionId.current);
  }, []);

  const sendMessage = async () => {
    const text = input.trim();

    if (!text || loading) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: text,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId.current,
          message: text,
          system_prompt: systemPrompt,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          metadata: data.metadata,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "error",
          content: `Error: ${error.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Lyftr AI</h1>
          <p>Resilient LLM Chatbot</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Backend Connected
        </div>
      </header>

      <main className="main">
        <aside className="sidebar">
          <h3>System Prompt</h3>

          <textarea
            data-testid="system-prompt-input"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="Set system instructions..."
          />

          <div className="info-card">
            <h3>Session</h3>
            <p>New session created on every page load.</p>
          </div>

          <div className="info-card">
            <h3>Features</h3>
            <p>✓ Multi-turn memory</p>
            <p>✓ Key failover</p>
            <p>✓ Response caching</p>
            <p>✓ Token tracking</p>
          </div>
        </aside>

        <section className="chat">
          <div className="messages">
            {messages.length === 0 && (
              <div className="welcome">
                <div className="logo">AI</div>
                <h2>How can I help you?</h2>
                <p>
                  Send a message to start a conversation.
                </p>
              </div>
            )}

            {messages.map((message, index) => {
              if (message.role === "user") {
                return (
                  <div className="message-row user-row" key={index}>
                    <div className="user-message">
                      {message.content}
                    </div>
                  </div>
                );
              }

              if (message.role === "error") {
                return (
                  <div className="error-message" key={index}>
                    ⚠ {message.content}
                  </div>
                );
              }

              return (
                <div
                  className="message-row assistant-row"
                  data-testid="assistant-message"
                  key={index}
                >
                  <div className="assistant-message">
                    <div className="assistant-label">
                      Lyftr AI
                    </div>

                    <div className="reply">
                      {message.content}
                    </div>

                    {message.metadata && (
                      <div className="metadata">
                        <span
                          className={
                            message.metadata.resolution_source ===
                            "LLM_CACHE"
                              ? "badge cache"
                              : "badge live"
                          }
                          data-testid="meta-source"
                        >
                          {message.metadata.resolution_source}
                        </span>

                        <span data-testid="meta-model">
                          Model: {message.metadata.model}
                        </span>

                        <span data-testid="meta-latency">
                          {message.metadata.latency_ms} ms
                        </span>

                        <span data-testid="meta-input-tokens">
                          Input: {message.metadata.input_tokens}
                        </span>

                        <span data-testid="meta-output-tokens">
                          Output: {message.metadata.output_tokens}
                        </span>

                        {message.metadata.key_id && (
                          <span>
                            Key: {message.metadata.key_id}
                          </span>
                        )}

                        <span>
                          Fallbacks:{" "}
                          {message.metadata.fallback_attempts}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="loading">
                <span></span>
                <span></span>
                <span></span>
              </div>
            )}
          </div>

          <div className="input-area">
            <textarea
              data-testid="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Lyftr AI..."
              rows="1"
            />

            <button
              data-testid="send-button"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
            >
              {loading ? "..." : "Send"}
            </button>
          </div>

          <div className="footer-text">
            Enter to send • Shift + Enter for new line
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;