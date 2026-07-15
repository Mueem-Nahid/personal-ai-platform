import Link from "next/link";
import { Button } from "@/components/atoms/Button";

export default function Home() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center">
      <h1 className="text-4xl font-bold">Career Agent</h1>
      <p className="mt-4 text-lg opacity-70">
        Offline personalized job-application agent.
      </p>
      <div className="mt-8 flex gap-4">
        <Link href="/profile">
          <Button variant="primary" size="lg">
            Profile Editor
          </Button>
        </Link>
        <Link href="/knowledge">
          <Button variant="secondary" size="lg">
            Knowledge Base
          </Button>
        </Link>
        <a href="http://localhost:8000/api/v1/docs">
          <Button variant="secondary" size="lg">
            API Docs
          </Button>
        </a>
      </div>
    </div>
  );
}
