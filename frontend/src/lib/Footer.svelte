<script lang="ts">
  import goLogo from "../assets/go-logo.svg";
  import svelteLogo from "../assets/svelte-logo.svg";
  import redisLogo from "../assets/redis-logo.svg";
  import flyLogo from "../assets/fly-logo.svg";
</script>

<p class="md:text-center md:mx-auto max-w-screen-sm">
  Built by <a href="mailto:ylau36@gatech.edu">Yee Ching Lau</a>, adapted from
  <a href="https://github.com/ekzhang/classes.wtf">Eric Zhang’s classes.wtf</a>.
  Powered by the
  <a href="https://github.com/gt-scheduler/crawler-v2">Georgia Tech crawler</a>
  to make a GT-specific version. Built with
  <a href="https://go.dev"><img src={goLogo} alt="Go" class="pb-1 pt-0.5" /></a>
  and
  <a href="https://svelte.dev"
    ><img src={svelteLogo} alt="Svelte" class="pb-0.5" /></a
  >, indexed with
  <a href="https://redis.io"><img src={redisLogo} alt="Redis" /></a>, and
  deployed to the edge on
  <a href="https://fly.io"><img src={flyLogo} alt="Fly.io" class="pb-0.5" /></a
  >.
  <a href="https://github.com/ekzhang/classes.wtf">Original code</a>.
</p>

<style lang="postcss">
  img {
    @apply inline-block h-6 px-0.5;
  }

  a {
    @apply text-blue-700 hover:underline;
  }
</style>
