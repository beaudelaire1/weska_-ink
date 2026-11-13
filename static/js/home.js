const initHomepage = () => {
  const carousel = document.querySelector("[data-product-carousel]");
  const reel = carousel?.querySelector(".product-reel");
  const scrollReel = (direction) => {
    if (!reel) return;
    const cards = Array.from(reel.querySelectorAll(".product-card"));
    const reelLeft = reel.getBoundingClientRect().left;
    const card = direction > 0
      ? cards.find((item) => item.getBoundingClientRect().left > reelLeft + 4)
      : [...cards].reverse().find((item) => item.getBoundingClientRect().left < reelLeft - 4);
    if (!card) return;
    const left = reel.scrollLeft + card.getBoundingClientRect().left - reelLeft;
    reel.scrollTo({ left: Math.max(0, left), behavior: "smooth" });
  };

  carousel?.addEventListener("click", (event) => {
    const control = event.target.closest("[data-carousel-prev], [data-carousel-next]");
    if (!control) return;
    event.preventDefault();
    scrollReel(control.hasAttribute("data-carousel-next") ? 1 : -1);
  });

  const gsap = window.gsap;
  const ScrollTrigger = window.ScrollTrigger;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!gsap || !ScrollTrigger || reduceMotion) return;

  gsap.registerPlugin(ScrollTrigger);

  const intro = gsap.timeline({ defaults: { ease: "power3.out" } });
  intro
    .from(".home-hero-topline", { autoAlpha: 0, y: 12, duration: 0.5 })
    .from(".home-kicker", { autoAlpha: 0, y: 15, duration: 0.55 }, "-=0.2")
    .from(".home-hero h1 span", { autoAlpha: 0, yPercent: 55, duration: 0.9, ease: "power4.out" }, "-=0.18")
    .from(".home-hero h1 em", { autoAlpha: 0, yPercent: 60, duration: 1, ease: "power4.out" }, "-=0.62")
    .from(".home-hero-copy>p", { autoAlpha: 0, y: 16, duration: 0.55 }, "-=0.42")
    .from(".home-hero-actions>*", { autoAlpha: 0, y: 12, duration: 0.48, stagger: 0.1 }, "-=0.3")
    .from(".home-hero-seal", { autoAlpha: 0, scale: 0.75, rotation: -14, duration: 0.7 }, "-=0.35")
    .from(".home-hero-bottom>*", { autoAlpha: 0, y: 10, duration: 0.4, stagger: 0.1 }, "-=0.3");

  gsap.fromTo(
    ".home-hero-image img",
    { scale: 1.17 },
    { scale: 1.08, duration: 1.8, ease: "power2.out", delay: 0.05 },
  );
  gsap.to(".home-hero-image img", {
    yPercent: 7,
    ease: "none",
    scrollTrigger: { trigger: ".home-hero", start: "top top", end: "bottom top", scrub: 0.8 },
  });
  gsap.to(".home-scroll-progress span", {
    scaleX: 1,
    ease: "none",
    scrollTrigger: { trigger: document.documentElement, start: "top top", end: "bottom bottom", scrub: 0.25 },
  });
  gsap.to(".home-hero-seal", {
    rotation: 22,
    ease: "none",
    scrollTrigger: { trigger: ".home-hero", start: "top top", end: "bottom top", scrub: 1.2 },
  });

  gsap.utils.toArray("[data-reveal]").forEach((element) => {
    gsap.fromTo(
      element,
      { autoAlpha: 0, y: 35, filter: "blur(5px)" },
      {
        autoAlpha: 1,
        y: 0,
        filter: "blur(0px)",
        duration: 0.9,
        ease: "power3.out",
        scrollTrigger: { trigger: element, start: "top 85%", once: true },
      },
    );
  });

  gsap.utils.toArray("[data-parallax] img").forEach((image) => {
    gsap.to(image, {
      yPercent: 8,
      ease: "none",
      scrollTrigger: { trigger: image.parentElement, start: "top bottom", end: "bottom top", scrub: 0.85 },
    });
  });

  gsap.fromTo(
    ".home-manifesto h2",
    { y: 42, autoAlpha: 0.45 },
    {
      y: -18,
      autoAlpha: 1,
      ease: "none",
      scrollTrigger: { trigger: ".home-manifesto", start: "top 80%", end: "bottom 30%", scrub: 0.8 },
    },
  );
  gsap.to(".home-manifesto-orbit", {
    rotation: 24,
    ease: "none",
    scrollTrigger: { trigger: ".home-manifesto", start: "top bottom", end: "bottom top", scrub: 1.2 },
  });
  gsap.to(".home-step-symbol", {
    y: -8,
    duration: 2.4,
    stagger: 0.24,
    repeat: -1,
    yoyo: true,
    ease: "sine.inOut",
  });

  const productCards = gsap.utils.toArray(".home-products .product-card");
  if (productCards.length) {
    gsap.fromTo(
      productCards,
      { autoAlpha: 0, y: 24 },
      {
        autoAlpha: 1,
        y: 0,
        duration: 0.65,
        stagger: 0.1,
        ease: "power3.out",
        scrollTrigger: { trigger: ".home-product-reel-shell", start: "top 86%", once: true },
      },
    );
  }

  gsap.to(".home-finale>img", {
    yPercent: 5,
    ease: "none",
    scrollTrigger: { trigger: ".home-finale", start: "top bottom", end: "bottom top", scrub: 0.8 },
  });
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initHomepage, { once: true });
} else {
  initHomepage();
}
