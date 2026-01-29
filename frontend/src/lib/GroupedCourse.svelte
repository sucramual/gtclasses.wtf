<script lang="ts">
  import GenEdAreas from "./GenEdAreas.svelte";
  import type { CourseData } from "./search";

  export type CourseGroup = {
    key: string;
    course: CourseData;
    sections: CourseData[];
  };

  export let group: CourseGroup;

  function meetingString(data: CourseData) {
    const schedules = [];
    for (const pattern of data.meetingPatterns) {
      let ret = "";
      if (pattern.meetsOnMonday) ret += "M";
      if (pattern.meetsOnTuesday) ret += "Tu";
      if (pattern.meetsOnWednesday) ret += "W";
      if (pattern.meetsOnThursday) ret += "Th";
      if (pattern.meetsOnFriday) ret += "F";
      if (pattern.meetsOnSaturday) ret += "S";
      if (pattern.meetsOnSunday) ret += "Su";
      if (!ret) continue;
      if (pattern.startTime) {
        ret += " " + pattern.startTime;
        if (pattern.endTime) {
          ret += "-" + pattern.endTime;
        }
      }
      schedules.push(ret);
    }
    if (schedules.length === 0) return "TBA";
    return schedules.join(", ");
  }

  function uniqueInstructors(sections: CourseData[]) {
    const seen = new Set<string>();
    const result: { name: string; email: string }[] = [];
    for (const section of sections) {
      for (const instructor of section.instructors) {
        const key = `${instructor.name}||${instructor.email}`;
        if (seen.has(key)) continue;
        seen.add(key);
        result.push(instructor);
      }
    }
    return result;
  }

  function sectionSort(a: CourseData, b: CourseData) {
    return a.classSection.localeCompare(b.classSection);
  }

  $: sectionsSorted = [...group.sections].sort(sectionSort);
  $: sectionLabels = sectionsSorted.map((section) => section.classSection);
  $: instructors = uniqueInstructors(sectionsSorted);
</script>

<div>
  <div class="flex gap-8">
    <div class="flex-1">
      <h3 class="text-sm font-bold">
        <span title={group.course.subjectDescription}
          >{group.course.subject}</span
        >
        {group.course.catalogNumber}: {group.course.title || "[No Title]"}
        ({group.course.semester})
      </h3>
      <p class="text-sm mb-1">
        {#each instructors as instructor, i}
          <a
            href={instructor.email
              ? `mailto:${instructor.email.toLowerCase()}`
              : undefined}>{instructor.name}</a
          >{#if i < instructors.length - 1}{", "}{/if}
        {/each}
      </p>
    </div>
    <div class="mt-0.5 hidden sm:block">
      <GenEdAreas value={group.course.genEdArea} />
    </div>
  </div>
  {#if group.course.genEdArea.length}
    <div class="mb-1.5 sm:hidden">
      <GenEdAreas value={group.course.genEdArea} />
    </div>
  {/if}
  <p class="text-xs font-light mb-1">
    Sections: {sectionLabels.join(", ")} | {group.course.level} |
    {group.course.component} | {group.course.campus}
  </p>
  <div class="text-xs mb-1">
    {@html group.course.description
      .replaceAll("&nbsp;", "\xa0")
      .replaceAll(/<p>\s*<\/p>/g, "")}
  </div>

  <details class="text-xs mt-2">
    <summary class="cursor-pointer text-gray-600">
      Show section details ({sectionsSorted.length})
    </summary>
    <div class="mt-2 space-y-2">
      {#each sectionsSorted as section (section.id)}
        <div class="rounded border border-gray-200 px-2 py-1">
          <div class="font-semibold">
            {section.classSection}
            {#if section.crn}
              <span class="font-normal text-gray-500">({section.crn})</span>
            {/if}
          </div>
          <div>
            {meetingString(section)} | {section.component} | {section.campus}
          </div>
          {#if section.instructors.length}
            <div class="text-gray-600">
              {#each section.instructors as instructor, i}
                <a
                  href={instructor.email
                    ? `mailto:${instructor.email.toLowerCase()}`
                    : undefined}>{instructor.name}</a
                >{#if i < section.instructors.length - 1}{", "}{/if}
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </details>
</div>
