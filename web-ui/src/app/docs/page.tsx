'use client';

import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Navigation from '@/components/Navigation';
import Footer from '@/components/Footer';

// Helper function to create slug from heading text
function slugify(text: string): string {
  return text
    .toString()
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-');
}

export default function DocsPage() {
  const [markdown, setMarkdown] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDocs() {
      try {
        const response = await fetch('/api/docs');
        if (!response.ok) {
          throw new Error('Failed to load documentation');
        }
        const data = await response.json();
        setMarkdown(data.content);
      } catch (err: any) {
        console.error('Failed to fetch documentation:', err);
        setError(err.message || 'Failed to load documentation');
      } finally {
        setLoading(false);
      }
    }

    fetchDocs();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navigation />

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Documentation</h2>
          <p className="text-gray-600">
            Complete user guide for the Nexus Dashboard MCP Server
          </p>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
            <p className="mt-2 text-gray-600">Loading documentation...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow p-8">
            <div className="prose prose-slate max-w-none prose-headings:text-gray-900 prose-p:text-gray-700 prose-strong:text-gray-900 prose-li:text-gray-700 prose-a:text-blue-600 prose-blockquote:text-gray-700 prose-th:text-gray-900 prose-td:text-gray-700 [&_pre]:!bg-[#1a1a2e] [&_pre]:!p-4 [&_pre_code]:!bg-transparent [&_pre_code]:!text-[#e0e0e0] [&_pre_code]:!p-0">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  h1: ({ children }) => {
                    const text = String(children);
                    const id = slugify(text);
                    return (
                      <h1 id={id} className="text-3xl font-bold text-gray-900 mb-4 mt-8 pb-2 border-b border-gray-200 scroll-mt-20">
                        {children}
                      </h1>
                    );
                  },
                  h2: ({ children }) => {
                    const text = String(children);
                    const id = slugify(text);
                    return (
                      <h2 id={id} className="text-2xl font-bold text-gray-900 mb-4 mt-8 scroll-mt-20">
                        {children}
                      </h2>
                    );
                  },
                  h3: ({ children }) => {
                    const text = String(children);
                    const id = slugify(text);
                    return (
                      <h3 id={id} className="text-xl font-bold text-gray-900 mb-3 mt-6 scroll-mt-20">
                        {children}
                      </h3>
                    );
                  },
                  h4: ({ children }) => {
                    const text = String(children);
                    const id = slugify(text);
                    return (
                      <h4 id={id} className="text-lg font-bold text-gray-900 mb-2 mt-4 scroll-mt-20">
                        {children}
                      </h4>
                    );
                  },
                  p: ({ children }) => (
                    <p className="text-gray-700 leading-7 mb-4">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc pl-6 mb-4 text-gray-700">
                      {children}
                    </ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal pl-6 mb-4 text-gray-700">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="text-gray-700 my-1">
                      {children}
                    </li>
                  ),
                  code: ({ className, children, ...props }) => {
                    const isInline = !className;
                    return isInline ? (
                      <code className="bg-gray-100 text-gray-800 px-1.5 py-0.5 rounded text-sm font-mono">
                        {children}
                      </code>
                    ) : (
                      <code className="block text-[#e0e0e0] font-mono text-sm whitespace-pre bg-transparent" {...props}>
                        {children}
                      </code>
                    );
                  },
                  pre: ({ children }) => (
                    <pre className="bg-[#1a1a2e] text-[#e0e0e0] p-4 rounded-lg overflow-x-auto mb-4 font-mono text-sm leading-relaxed border-0">
                      {children}
                    </pre>
                  ),
                  a: ({ href, children }) => {
                    // Check if it's an internal anchor link
                    const isAnchor = href?.startsWith('#');
                    return (
                      <a
                        href={href}
                        className="text-blue-600 hover:underline"
                        {...(!isAnchor && { target: "_blank", rel: "noopener noreferrer" })}
                      >
                        {children}
                      </a>
                    );
                  },
                  strong: ({ children }) => (
                    <strong className="font-semibold text-gray-900">
                      {children}
                    </strong>
                  ),
                  em: ({ children }) => (
                    <em className="italic text-gray-700">
                      {children}
                    </em>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-700 my-4">
                      {children}
                    </blockquote>
                  ),
                  table: ({ children }) => (
                    <div className="overflow-x-auto mb-4">
                      <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
                        {children}
                      </table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead className="bg-gray-50">
                      {children}
                    </thead>
                  ),
                  tbody: ({ children }) => (
                    <tbody className="bg-white divide-y divide-gray-200">
                      {children}
                    </tbody>
                  ),
                  tr: ({ children }) => (
                    <tr>
                      {children}
                    </tr>
                  ),
                  th: ({ children }) => (
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-900 uppercase tracking-wider">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="px-4 py-2 text-sm text-gray-700">
                      {children}
                    </td>
                  ),
                  hr: () => (
                    <hr className="my-8 border-gray-200" />
                  ),
                }}
              >
                {markdown}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
