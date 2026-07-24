document.addEventListener("DOMContentLoaded", function () {
    const path = window.location.pathname;
    let title = "Md. Abu Bokkor Shiddik | Researcher";
    let desc = "Academic portfolio and research showcase of Md. Abu Bokkor Shiddik.";
    let keys = "Abu Bokkor Shiddik, Researcher, Data Science";

    // Dynamic routing based on the filename in the URL
    if (path.includes("index") || path.includes("home") || path === "/" || path.endsWith("/")) {
        title = "Md. Abu Bokkor Shiddik | Machine Learning & Global Health Researcher";
        desc = "Academic portfolio and research showcase of Md. Abu Bokkor Shiddik. Specializing in Machine Learning, Explainable AI (XAI), and Spatiotemporal Disease Modeling at BRUR.";
        keys += ", Machine Learning, Public Health, XAI, BRUR";
    } else if (path.includes("publications")) {
        title = "Publications & Research Papers | Md. Abu Bokkor Shiddik";
        desc = "Peer-reviewed scientific publications on climate-health interactions, global malaria patterns, and interpretable dengue early warning systems.";
        keys += ", Scientific Reports, BMJ Open, Research Papers, Disease Prediction";
        addMeta("citation_author", "Shiddik, Md. Abu Bokkor");
        addMeta("citation_author_institution", "Begum Rokeya University, Rangpur");
    } else if (path.includes("projects") || path.includes("data-code")) {
        title = "Projects, Code & Open Data Labs | Md. Abu Bokkor Shiddik";
        desc = "Explore open-source data labs, GitHub repositories, and interactive early warning visualization dashboards for epidemiological modeling.";
        keys += ", Dengue Dataset, R Packages, Open Data, Time-series";
    } else if (path.includes("R-programming") || path.includes("Learn-R") || path.includes("r-")) {
        title = "Learn R Programming Notes | Data Science Hub";
        desc = "Master R programming for statistics and data science. Step-by-step guides, code syntaxes, and data visualization notes.";
        keys += ", R syntax, ggplot2, dataframes, programming notes";
    } else if (path.includes("Python-programming") || path.includes("py-")) {
        title = "Learn Python Programming Notes | Data Science Hub";
        desc = "Comprehensive Python tutorials for data analysis, programming fundamentals, and machine learning pipelines.";
        keys += ", Python data science, pandas, numpy, matplotlib";
    } else if (path.includes("SQL-programming") || path.includes("sql-")) {
        title = "Learn SQL Programming Notes | Database Analytics";
        desc = "Structured SQL programming guides covering window functions, CTEs, aggregates, and data query filtering.";
        keys += ", SQL Joins, window functions, database syntax";
    } else if (path.includes("courses") || path.includes("BSc") || path.includes("MSc")) {
        title = "Academic Coursework Curriculum | Department of Statistics, BRUR";
        desc = "Academic syllabi and course structures for B.Sc. and M.Sc. in Statistics and Statistical Genomics at Begum Rokeya University, Rangpur.";
        keys += ", STAT 5103, Statistical Genomics, BRUR courses";
    }

    // Apply tags directly into the document
    document.title = title;
    addMeta("description", desc);
    addMeta("keywords", keys);
    addMeta("author", "Md. Abu Bokkor Shiddik");
    addMeta("robots", "index, follow");
    
    // Open Graph Social Media Previews
    addOGMeta("og:title", title);
    addOGMeta("og:description", desc);
    addOGMeta("og:url", window.location.href);
    addOGMeta("og:image", "https://github.io");

    function addMeta(name, content) {
        let meta = document.createElement('meta');
        meta.name = name;
        meta.content = content;
        document.head.appendChild(meta);
    }
    function addOGMeta(property, content) {
        let meta = document.createElement('meta');
        meta.setAttribute('property', property);
        meta.content = content;
        document.head.appendChild(meta);
    }
});
