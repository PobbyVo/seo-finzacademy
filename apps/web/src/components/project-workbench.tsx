"use client";

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { api, ApiError, type Project, type Topic } from "@/lib/api";

type Connection = "checking" | "online" | "offline";

function rememberSelection(project: Project) {
  const url = new URL(window.location.href);
  url.searchParams.set("project", project.id);
  window.history.replaceState(null, "", url);
}

function asApiError(error: unknown) {
  return error instanceof ApiError
    ? error
    : new ApiError("Chưa thể hoàn tất thao tác.", "Vui lòng thử kết nối lại.");
}

function savedTime(value: string) {
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function ProjectWorkbench() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [name, setName] = useState("");
  const [topicCode, setTopicCode] = useState("");
  const [connection, setConnection] = useState<Connection>("checking");
  const [pending, setPending] = useState<string | null>("Đang kết nối API local…");
  const [error, setError] = useState<ApiError | null>(null);
  const [notice, setNotice] = useState("");
  const connectionGeneration = useRef(0);

  const connect = useCallback(() => {
    const generation = ++connectionGeneration.current;
    return Promise.all([api.health(), api.projects(), api.topics()]).then(([, projectData, topicData]) => {
      if (generation !== connectionGeneration.current) return;
      const requestedId = new URL(window.location.href).searchParams.get("project");
      const project =
        projectData.projects.find((item) => item.id === requestedId) ??
        projectData.projects[0] ??
        null;
      setProjects(projectData.projects);
      setTopics(topicData.topics);
      setSelected(project);
      setTopicCode("");
      setConnection("online");
      if (project) rememberSelection(project);
    }).catch((cause: unknown) => {
      if (generation !== connectionGeneration.current) return;
      setConnection("offline");
      setError(asApiError(cause));
    }).finally(() => {
      if (generation === connectionGeneration.current) setPending(null);
    });
  }, []);

  function reconnect() {
    setPending("Đang kết nối API local…");
    setError(null);
    setConnection("checking");
    void connect();
  }

  useEffect(() => {
    void connect();
    return () => { connectionGeneration.current += 1; };
  }, [connect]);

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending("Đang lưu dự án trống…");
    setError(null);
    setNotice("");
    try {
      const project = await api.createProject(name);
      setProjects((current) => [project, ...current]);
      setSelected(project);
      setName("");
      setTopicCode("");
      rememberSelection(project);
      setNotice("Đã tạo dự án trống và lưu trên máy.");
    } catch (cause) {
      setError(asApiError(cause));
    } finally {
      setPending(null);
    }
  }

  async function chooseProject(id: string) {
    setPending("Đang mở dự án…");
    setError(null);
    setNotice("");
    try {
      const project = await api.project(id);
      setSelected(project);
      setTopicCode("");
      rememberSelection(project);
    } catch (cause) {
      setError(asApiError(cause));
    } finally {
      setPending(null);
    }
  }

  async function loadDemo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    setPending("Đang nạp fixture demo…");
    setError(null);
    setNotice("");
    try {
      const project = await api.loadDemo(selected.id, topicCode);
      setSelected(project);
      setProjects((current) => current.map((item) => (item.id === project.id ? project : item)));
      setNotice("Đã nạp dữ liệu minh họa. Chưa có phân tích AI hay bằng chứng SEO.");
    } catch (cause) {
      setError(asApiError(cause));
    } finally {
      setPending(null);
    }
  }

  const disabled = pending !== null || connection !== "online";

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">Đến nội dung chính</a>
      <header className="topbar">
        <div className="brand"><span className="brand-mark" aria-hidden="true">F<span>.</span></span><div><strong>FINZ</strong><span className="brand-subtitle">SEO ASSISTANT</span></div></div>
        <div className="topbar-meta"><span className="local-tag">LOCAL</span><span className="milestone-tag">Milestone 0</span></div>
      </header>

      <div className="demo-banner"><span className="demo-indicator" aria-hidden="true" /><strong>DEMO - CHƯA PHÂN TÍCH AI THỰC</strong><span className="demo-description">Dữ liệu minh họa · Lưu trên máy của bạn</span></div>

      <main id="main" className="main-container">
        <div className="page-heading"><div><p className="eyebrow">KHÔNG GIAN LÀM VIỆC</p><h1>Dự án của bạn</h1><p className="page-description">Bắt đầu từ dự án trống hoặc khám phá một chủ đề demo.</p></div><div className={`connection connection-${connection}`} role="status"><span aria-hidden="true" />{connection === "online" ? "API local · SQLite đã kết nối" : connection === "offline" ? "API local chưa kết nối" : "Đang kiểm tra kết nối…"}</div></div>

        {error && <div className="error-panel" role="alert"><div><strong>{error.message}</strong><p>{error.nextAction}</p>{error.requestId && <small>Mã yêu cầu: {error.requestId}</small>}</div><button className="button button-secondary" onClick={reconnect} disabled={pending !== null}>Thử kết nối lại</button></div>}
        <div className="feedback" role="status" aria-live="polite">{pending || notice}</div>

        <div className="workspace-grid">
          <aside className="project-sidebar" aria-label="Danh sách dự án">
            <div className="section-heading"><h2>Dự án local</h2><span className="count-badge">{projects.length}</span></div>
            <div className="project-list">
              {projects.length === 0 ? <p className="sidebar-empty">{pending ? "Đang đọc dữ liệu…" : "Chưa có dự án. Tạo dự án đầu tiên ở bên dưới."}</p> : projects.map((project) => <button key={project.id} type="button" className={`project-item ${selected?.id === project.id ? "project-item-selected" : ""}`} aria-label={`Mở dự án ${project.name}`} aria-pressed={selected?.id === project.id} disabled={disabled} onClick={() => void chooseProject(project.id)}><span className="project-icon" aria-hidden="true">▤</span><span className="project-item-text"><strong>{project.name}</strong><small>{project.topic ? `${project.topic.topic_code} · ${project.topic.topic_name}` : "Dự án trống"}</small></span><span className="project-arrow" aria-hidden="true">›</span></button>)}
            </div>
            <form className="create-form" onSubmit={(event) => void createProject(event)}>
              <label htmlFor="project-name">Tên dự án</label>
              <input id="project-name" type="text" placeholder="Ví dụ: Nghiên cứu nội dung" value={name} onChange={(event) => setName(event.target.value)} maxLength={120} required disabled={disabled} autoComplete="off" />
              <button className={`button ${selected ? "button-secondary" : "button-primary"} w-full`} type="submit" disabled={disabled || !name.trim()}><span aria-hidden="true">＋</span> Tạo dự án</button>
              <p>Chỉ tạo dự án trống. Chưa nhập taxonomy hoặc từ khóa.</p>
            </form>
            <div className="storage-note"><span aria-hidden="true">◉</span><p>Dữ liệu lưu bằng SQLite.<br />Các dự án được lưu độc lập.</p></div>
          </aside>

          <section className="project-content" aria-label="Chi tiết dự án">
            {!selected ? <div className="empty-workspace"><div className="empty-illustration" aria-hidden="true"><span>▤</span><i>＋</i></div><p className="eyebrow">KHỞI ĐẦU TỪ NGUỒN DỮ LIỆU</p><h2>Một không gian cho mỗi chủ đề</h2><p>Tạo dự án ở cột bên cạnh. Bạn có thể giữ dự án trống hoặc chủ động nạp dữ liệu mẫu để xem cấu trúc.</p><div className="empty-detail"><span aria-hidden="true">✓</span> Chạy local, không cần tài khoản hay API key</div></div> : <>
              <div className="project-header"><div><div className="project-title-line"><h2>{selected.name}</h2><span className="draft-badge">BẢN NHÁP</span></div><p>Lưu lúc {savedTime(selected.updated_at)} · Phiên bản {selected.version}</p></div><span className="subtle-tag">{selected.topic ? "NGUỒN: FIXTURE DEMO" : "CHƯA CÓ CHỦ ĐỀ"}</span></div>

              {!selected.topic ? <div className="setup-area"><div className="setup-icon" aria-hidden="true">↗</div><h3>Dự án chưa có dữ liệu chủ đề</h3><p>Dự án đã được lưu. Để xem dữ liệu minh họa, chọn một chủ đề rồi bấm <strong>Nạp demo</strong>.</p><form className="demo-form" onSubmit={(event) => void loadDemo(event)}><div><label htmlFor="demo-topic">Chủ đề demo</label><select id="demo-topic" required value={topicCode} onChange={(event) => setTopicCode(event.target.value)} disabled={disabled}><option value="">Chọn chủ đề minh họa</option>{topics.map((topic) => <option key={topic.topic_code} value={topic.topic_code}>{topic.topic_code} · {topic.topic_name}</option>)}</select></div><button className="button button-primary" type="submit" disabled={disabled || !topicCode}>Nạp demo <span aria-hidden="true">→</span></button></form><p className="helper-note">Nạp demo chỉ thêm fixture vào dự án đang chọn. Chưa xác minh nhu cầu tìm kiếm hoặc chỉ số SEO.</p></div> : <div className="loaded-data">
                <div className="topic-heading"><div><p className="eyebrow">TOPIC PILLAR · DỮ LIỆU MINH HỌA</p><h3>{selected.topic.topic_code} · {selected.topic.topic_name}</h3></div><span className="demo-pill">DEMO</span></div>
                <dl className="taxonomy-grid"><div><dt>Pillar</dt><dd>{selected.topic.pillar}</dd></div><div><dt>Loại topic</dt><dd>{selected.topic.topic_type}</dd></div><div><dt>Trục chia của pillar</dt><dd>{selected.topic.pillar_axis}</dd></div><div><dt>Chủ đề chính bên trong</dt><dd>{selected.topic.main_topics.join(" / ")}</dd></div></dl>

                <div className="data-section"><div className="section-heading"><h4>Mã nội dung nguồn</h4><span className="count-badge">{selected.content_codes.length}</span></div>{selected.content_codes.length ? <div className="content-code-list">{selected.content_codes.map((code) => <article className="content-code" key={code.source_ref}><span className="code-tag">{code.content_code}</span><div><h5>{code.content_topic}</h5><p>{code.original_title}</p></div></article>)}</div> : <p className="muted-info">Fixture này chưa có mã nội dung hoặc từ khóa nguồn.</p>}</div>

                {selected.source_keywords.length > 0 && <div className="data-section"><div className="section-heading"><h4>Từ khóa nguồn</h4><span className="count-badge">{selected.source_keywords.length}</span></div><p className="table-description">Giai đoạn funnel là dữ liệu nguồn; Semrush Intent chưa có dữ liệu.</p><div className="table-scroll" tabIndex={0} role="region" aria-label="Bảng từ khóa có thể cuộn ngang"><table><caption className="sr-only">Từ khóa nguồn demo</caption><thead><tr><th>Từ khóa / Mã nội dung</th><th>Vai trò</th><th>Giai đoạn</th><th>Volume</th><th>KD</th><th>Semrush Intent</th><th>SERP</th></tr></thead><tbody>{selected.source_keywords.map((keyword) => <tr key={keyword.source_ref}><td><strong>{keyword.keyword}</strong><small>{keyword.content_code}</small></td><td>{keyword.role}</td><td><span className="funnel-tag">{keyword.funnel}</span></td><td>{keyword.volume ?? <span className="missing-value">Chưa có dữ liệu</span>}</td><td>{keyword.kd ?? <span className="missing-value">Chưa có dữ liệu</span>}</td><td>{keyword.intent ?? <span className="missing-value">Chưa có dữ liệu</span>}</td><td>{keyword.serp ?? <span className="missing-value">Chưa có dữ liệu</span>}</td></tr>)}</tbody></table></div></div>}

                <details className="source-details"><summary>Nguồn dữ liệu & snapshot</summary><dl><dt>Taxonomy source</dt><dd>{selected.topic.source_ref}</dd><dt>Snapshot</dt><dd>{selected.snapshot_id}</dd><dt>Mã nội dung & từ khóa</dt><dd>{[...selected.content_codes, ...selected.source_keywords].map((item) => <code key={item.source_ref}>{item.source_ref}</code>)}</dd></dl></details>
              </div>}

              <div className="scope-note"><span className="scope-icon" aria-hidden="true">i</span><p><strong>Phạm vi M0: nền tảng local & dữ liệu demo.</strong><br />Nhập taxonomy, phân tích SEO, nhận file và xuất brief chưa được triển khai.</p></div>
            </>}
          </section>
        </div>
        <footer className="page-footer"><span>FINZ SEO Assistant · M0</span><span>Next.js + FastAPI + SQLite</span></footer>
      </main>
    </div>
  );
}
