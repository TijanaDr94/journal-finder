"""
Journal scope definitions copied from MDPI journal about pages.
Each entry contains structured metadata used for both BM25 and LLM-based scoring.
"""

from dataclasses import dataclass, field


@dataclass
class Journal:
    """ Metadata and scope description for a single MDPI journal."""
    id: str
    name: str
    issn: str
    url: str
    scope: str
    keywords: list[str] = field(default_factory=list)


JOURNALS: list[Journal] = [
    Journal(
        id="molecules",
        name="Molecules",
        issn="1420-3049",
        url="https://www.mdpi.com/journal/molecules",
        scope=(
            "Molecules (ISSN 1420-3049, CODEN: MOLEFW) provides an advanced forum "
            "for science of chemistry and all interfacing disciplines. The journal "
            "aims to provide rigorous peer review and rapid publication of cutting-edge "
            "research to educate and inspire the scientific community worldwide. "
            "Scientists are encouraged to publish experimental and theoretical results "
            "in as much detail as possible to ensure reproducibility. "
            "Main research areas include, but are not limited to: "
            "organic chemistry, medicinal chemistry, natural products chemistry, "
            "inorganic chemistry, physical chemistry, materials science, nanoscience, "
            "catalysis, chemical biology, analytical chemistry, supramolecular chemistry, "
            "theoretical chemistry, green chemistry, and photochemistry."
        ),
        keywords=[
            "organic chemistry", "medicinal chemistry", "natural products chemistry",
            "inorganic chemistry", "physical chemistry", "materials science",
            "nanoscience", "catalysis", "chemical biology", "analytical chemistry",
            "supramolecular chemistry", "theoretical chemistry", "green chemistry",
            "photochemistry",
        ],
    ),
    Journal(
        id="ai",
        name="AI",
        issn="2673-2688",
        url="https://www.mdpi.com/journal/ai",
        scope=(
            "AI (ISSN 2673-2688) is an international and interdisciplinary scholarly "
            "open access journal on artificial intelligence. The journal publishes "
            "original research articles, reviews, and communications that offer "
            "substantial new insight into any field involving artificial intelligence (AI). "
            "The journal encourages scientists and engineers to publish experimental "
            "and theoretical research in as much detail as possible to ensure "
            "reproducibility of results. "
            "Scope areas include: AI applications, AI techniques, AI theory, AI ethics, "
            "AI planning, artificial neural networks, natural language processing, "
            "computer and machine vision, intelligent machines and agents, machine learning, "
            "deep learning, robotics, genetic algorithms, knowledge representation and reasoning, "
            "evolutionary computing, expert systems, and Internet of Things (IoT)."
        ),
        keywords=[
            "artificial intelligence", "AI application", "AI technique", "AI theory",
            "AI ethics", "AI planning", "artificial neural networks", "natural language processing",
            "computer vision", "machine vision", "intelligent agent", "machine learning",
            "deep learning", "robotics", "genetic algorithms", "knowledge representation",
            "reasoning", "evolutionary computing", "expert systems", "Internet of Things", "IoT",
        ],
    ),
    Journal(
        id="physics",
        name="Physics",
        issn="2624-8174",
        url="https://www.mdpi.com/journal/physics",
        scope=(
            "Physics (ISSN 2624-8174) is an international, peer-reviewed, open access "
            "journal presenting the latest research on all aspects of physics ranging "
            "from fundamental studies to emerging technologies. The journal publishes "
            "reviews, regular research papers, short communications, and Special Issues "
            "on particular subjects. "
            "The journal encourages scientists to publish experimental and theoretical "
            "studies in as much detail as possible to ensure reproducibility of results. "
            "Scope areas include: acoustics; applied physics, instrumentation, and technologies; "
            "astronomy and astrophysics; atmospheric and climate physics; atomic and molecular physics; "
            "biological and medical physics; chemical physics; computational and data science; "
            "condensed matter physics; cosmic rays; fluid dynamics; geophysics and planetology; "
            "gravitation and cosmology; high-energy and particle physics; machine learning; "
            "magnetism; materials science; mathematical physics; mechanics; mesoscopics; "
            "nanophysics; networks and complex systems; nonlinear dynamics; nuclear physics; "
            "optics and photonics; plasma physics; quantum physics and quantum information; "
            "semiconductor physics; soft matter physics; solar physics; statistical physics "
            "and thermodynamics; superconductivity and superfluidity."
        ),
        keywords=[
            "acoustics", "applied physics", "instrumentation", "astronomy", "astrophysics",
            "atmospheric physics", "climate physics","atomic physics", "molecular physics",
            "biological physics", "medical physics", "chemical physics", "computational physics",
            "data science", "condensed matter physics", "cosmic rays", "fluid dynamics",
            "geophysics", "planetology", "gravitation", "cosmology", "particle physics",
            "high-energy physics", "machine learning", "magnetism", "materials science",
            "mathematical physics", "mechanics", "mesoscopics", "nanophysics", "complex systems",
            "nonlinear dynamics", "nuclear physics", "optics", "photonics", "plasma physics",
            "quantum physics", "quantum information", "semiconductor physics", "soft matter physics",
            "solar physics", "statistical physics", "thermodynamics", "superconductivity", "superfluidity",
        ],
    ),
    Journal(
        id="energies",
        name="Energies",
        issn="1996-1073",
        url="https://www.mdpi.com/journal/energies",
        scope=(
            "Energies (ISSN 1996-1073) is an open access journal publishing papers "
            "on scientific research, technology development, engineering policy, "
            "and management studies related to the general field of energy. "
            "The journal covers topics ranging from technological problems in energy "
            "supply, conversion, dispatch, and final use to the thermodynamics of "
            "the physical and chemical processes behind such technologies. "
            "The journal encourages scientists to publish experimental, numerical, "
            "and theoretical results in as much detail as possible to ensure "
            "reproducibility. "
            "Scope areas include: energy and environment, sustainable transition, "
            "bioenergy, clean energy, the hydrogen energy chain, distributed energy systems, "
            "energy and climate change, carbon emission and utilization, recycling of "
            "material and energy streams, sustainability analysis metrics, energy storage "
            "and applications, advanced energy materials, batteries, fuel cells, capacitors, "
            "micro- and nanoenergy conversion systems, energy and buildings, smart cities "
            "and urban management, phase change materials for energy storage, electrical engineering, "
            "electric vehicles, smart grids and microgrids, power electronics, electrical power systems, "
            "energy sources including wind, solar, hydro, fossil, nuclear, geothermal, "
            "ocean thermal, wave and tidal energy, energy conversion fundamentals, "
            "heat and mass transfer, thermodynamics, entropy analysis, exergy analysis, "
            "diagnostics and prognostics of energy conversion chains, artificial intelligence "
            "in energy systems design and control, monitoring and control systems, "
            "chemical energy, fuels, energy and combustion science, petroleum engineering, "
            "new working fluids for energy applications, energy economics and policy, "
            "and energy use in industry."
        ),
        keywords=[
            "energy", "sustainable transition", "bioenergy", "clean energy", "hydrogen energy",
            "distributed energy systems", "energy and climate change", "carbon emission",
            "carbon utilization", "recycling", "sustainability analysis", "energy storage",
            "advanced energy materials", "batteries", "fuel cells", "capacitors",
            "nanoenergy conversion", "energy and buildings", "smart cities","urban management",
            "phase change materials", "electrical engineering", "electric vehicles", "smart grids",
            "microgrids", "power electronics", "power systems", "wind energy", "solar energy",
            "hydro energy", "fossil energy", "nuclear energy", "geothermal energy", "wave energy",
            "tidal energy", "energy conversion", "heat transfer", "mass transfer", "thermodynamics",
            "entropy analysis", "exergy analysis", "energy diagnostics", "monitoring systems",
            "control systems", "chemical energy", "fuels", "combustion science", "petroleum engineering",
            "energy economics", "energy policy", "industrial energy use",
        ],
    ),
]

JOURNAL_MAP: dict[str, Journal] = {journal.id: journal for journal in JOURNALS}
