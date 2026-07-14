import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">Career Agent</h1>
      <p className="mt-4 text-lg opacity-70">
        Offline personalized job-application agent.
      </p>
      <div className="mt-8 flex gap-4">
        <Link
          href="/profile"
          className="rounded-lg bg-blue-600 px-6 py-3 text-white hover:bg-blue-700"
        >
          Profile Editor
        </Link>
        <Link
          href="http://localhost:8000/api/v1/docs"
          className="rounded-lg border px-6 py-3 hover:bg-gray-100 dark:hover:bg-gray-800"
        >
          API Docs
        </Link>
      </div>
    </main>
  );
}
