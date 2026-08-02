export type Role = "Docente" | "Estudiante";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: Message[];
}
