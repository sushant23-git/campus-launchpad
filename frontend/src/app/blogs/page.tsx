"use client";

import React, { useState } from "react";
import Sidebar from "../../components/Sidebar";
import { FileText, Search, User, Calendar, BookOpen, PenTool, Sparkles } from "lucide-react";

interface BlogPost {
  id: number;
  title: string;
  excerpt: string;
  author: string;
  role: string;
  date: string;
  category: string;
  readTime: string;
}

export default function BlogsHubPage() {
  const [search, setSearch] = useState("");
  const [blogs, setBlogs] = useState<BlogPost[]>([
    {
      id: 1,
      title: "Deep Dive into FastAPI Async Database Operations",
      excerpt: "How we leveraged SQLAlchemy 2.0 with aiosqlite and asyncpg to build non-blocking database layers in NOXUS.",
      author: "Sushant Gajbhiye",
      role: "Backend Architect",
      date: "Aug 18, 2026",
      category: "Backend",
      readTime: "6 min read",
    },
    {
      id: 2,
      title: "Mastering Tailwind CSS and Responsive Geometry",
      excerpt: "Best practices for implementing rounded SaaS layouts (8px rounded corners) and professional color tokens.",
      author: "Arpit Kumar",
      role: "Frontend Designer",
      date: "Aug 17, 2026",
      category: "Design System",
      readTime: "4 min read",
    },
    {
      id: 3,
      title: "Grounded AI: Training Custom LLMs for Sandbox Feedback",
      excerpt: "How our progress coach maps weekly activity data into personalized, structured execution hints.",
      author: "Chaitanya Program Lead",
      role: "AI & Program Architect",
      date: "Aug 16, 2026",
      category: "AI / ML",
      readTime: "8 min read",
    },
    {
      id: 4,
      title: "Continuous Delivery: Deploying Monorepos to Vercel",
      excerpt: "Troubleshooting path aliases and deploying serverless Python functions alongside Next.js under the same domain.",
      author: "Krish DevOps",
      role: "DevOps Engineer",
      date: "Aug 15, 2026",
      category: "DevOps",
      readTime: "5 min read",
    },
  ]);

  const [newTitle, setNewTitle] = useState("");
  const [newExcerpt, setNewExcerpt] = useState("");
  const [newCategory, setNewCategory] = useState("Backend");
  const [showAddForm, setShowAddForm] = useState(false);

  const handleCreatePost = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newExcerpt) return;

    const newPost: BlogPost = {
      id: Date.now(),
      title: newTitle,
      excerpt: newExcerpt,
      author: "You (Alice Student)",
      role: "Cohort Student",
      date: "Just now",
      category: newCategory,
      readTime: "3 min read",
    };

    setBlogs([newPost, ...blogs]);
    setNewTitle("");
    setNewExcerpt("");
    setShowAddForm(false);
  };

  const filteredBlogs = blogs.filter(
    (b) =>
      b.title.toLowerCase().includes(search.toLowerCase()) ||
      b.excerpt.toLowerCase().includes(search.toLowerCase()) ||
      b.author.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex bg-slate-950 min-h-screen text-slate-100">
      <Sidebar />

      <main className="flex-grow p-8 max-w-6xl">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight">Blogs Hub</h1>
            <p className="text-slate-400 mt-1 text-sm">
              Knowledge sharing center for technical guides, student builds, and insights.
            </p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs py-2.5 px-5 rounded-lg transition-all flex items-center gap-2"
          >
            <PenTool className="w-4 h-4" />
            Write Technical Guide
          </button>
        </header>

        {/* Add Blog Post Form */}
        {showAddForm && (
          <form
            onSubmit={handleCreatePost}
            className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-8 space-y-4 animate-fade-in"
          >
            <h3 className="text-lg font-bold text-slate-200">Publish to Cohort</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="text-2xs font-bold text-slate-400 uppercase">Title</label>
                <input
                  type="text"
                  placeholder="e.g. Setting up Docker local variables"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-lg px-4 py-2.5 text-sm mt-1 text-slate-200"
                  required
                />
              </div>
              <div>
                <label className="text-2xs font-bold text-slate-400 uppercase">Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-lg px-4 py-2.5 text-sm mt-1 text-slate-200"
                >
                  <option value="Backend">Backend</option>
                  <option value="Frontend">Frontend</option>
                  <option value="DevOps">DevOps</option>
                  <option value="AI / ML">AI / ML</option>
                  <option value="Design System">Design System</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-2xs font-bold text-slate-400 uppercase">Excerpt</label>
              <textarea
                placeholder="Give a brief summary of what your technical guide covers..."
                value={newExcerpt}
                onChange={(e) => setNewExcerpt(e.target.value)}
                className="w-full bg-slate-950 border border-slate-850 focus:border-blue-600 focus:outline-none rounded-lg px-4 py-2.5 text-sm mt-1 h-20 text-slate-200"
                required
              />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs py-2 px-4 rounded-lg transition-all"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs py-2 px-4 rounded-lg transition-all"
              >
                Publish Guide
              </button>
            </div>
          </form>
        )}

        {/* Search */}
        <div className="relative mb-8">
          <Search className="absolute left-3.5 top-3.5 text-slate-500 w-5 h-5" />
          <input
            type="text"
            placeholder="Search guides by title, category, or cohort author..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 focus:border-blue-600 focus:outline-none rounded-xl py-3.5 pl-12 pr-4 text-sm text-slate-200"
          />
        </div>

        {/* Blog Post List */}
        <section className="space-y-6">
          {filteredBlogs.map((blog) => (
            <article
              key={blog.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-6 transition-all hover:border-slate-700 hover:shadow-lg"
            >
              <div className="flex flex-wrap gap-2 items-center justify-between mb-3">
                <span className="text-2xs font-bold bg-blue-600/10 text-blue-400 px-2 py-1 rounded">
                  {blog.category}
                </span>
                <div className="flex items-center gap-4 text-2xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" /> {blog.date}
                  </span>
                  <span className="flex items-center gap-1">
                    <BookOpen className="w-3.5 h-3.5" /> {blog.readTime}
                  </span>
                </div>
              </div>

              <h3 className="text-lg font-bold text-slate-200 mb-2 hover:text-blue-400 cursor-pointer transition-all">
                {blog.title}
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed mb-4">{blog.excerpt}</p>

              <div className="flex items-center justify-between pt-4 border-t border-slate-850">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400 text-xs font-bold">
                    {blog.author[0]}
                  </div>
                  <div>
                    <span className="text-xs font-bold text-slate-200 block">{blog.author}</span>
                    <span className="text-4xs text-slate-400 font-medium uppercase tracking-wider block">
                      {blog.role}
                    </span>
                  </div>
                </div>
                <button className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-all">
                  Read Full Post →
                </button>
              </div>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
