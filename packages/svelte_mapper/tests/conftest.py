"""
Shared fixtures for svelte_mapper tests.
All Svelte/TS source content is defined here as string constants so tests
are fully self-contained — no real filesystem Svelte project required.
"""
import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Raw source snippets
# ---------------------------------------------------------------------------

SIMPLE_BUTTON_SVELTE = """\
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ButtonVariant } from '$lib/types';
  import Spinner from './Spinner.svelte';

  export let label: string = 'Click me';
  export let disabled: boolean = false;
  export let variant: ButtonVariant = 'primary';

  const dispatch = createEventDispatcher();

  function handleClick() {
    dispatch('click', { label });
  }
</script>

<button on:click={handleClick} {disabled}>
  <slot name="icon" />
  {label}
  <slot />
</button>
"""

DATA_TABLE_SVELTE = """\
<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Pagination from './Pagination.svelte';
  import SortIcon from './SortIcon.svelte';
  import { tableStore } from '$lib/stores/tableStore';

  export let items: Item[] = [];
  export let pageSize: number = 10;
  export let sortable: boolean = true;

  let currentPage = 0;

  onMount(() => tableStore.init());
  onDestroy(() => tableStore.reset());

  function handleSort(col: string) {
    tableStore.update(s => ({ ...s, sortCol: col }));
  }
</script>

{#each $tableStore.rows as row}
  <tr on:click={() => dispatch('rowClick', row)}>
    <slot name="row" {row} />
  </tr>
{/each}

<Pagination bind:currentPage {pageSize} on:pageChange />
"""

LAYOUT_SVELTE = """\
<script lang="ts">
  import Header from './Header.svelte';
  import Sidebar from './Sidebar.svelte';
  import { authStore } from '$lib/stores/authStore';
  import { themeStore } from '$lib/stores/themeStore';

  export let title: string = 'App';
</script>

<svelte:head>
  <title>{title}</title>
</svelte:head>

<Header {title} on:logout />
<Sidebar />
<slot />
"""

NO_EXPORTS_SVELTE = """\
<script lang="ts">
  import { writable } from 'svelte/store';
  const count = writable(0);
</script>

<button on:click={() => $count++}>
  Count: {$count}
</button>
"""

EMPTY_SVELTE = """\
<div>Hello</div>
"""

TABLE_STORE_TS = """\
import { writable, derived } from 'svelte/store';
import type { TableState } from '$lib/types';

const initialState: TableState = { rows: [], sortCol: null, page: 0 };

export const tableStore = writable<TableState>(initialState);
export const sortedRows = derived(tableStore, $s => [...$s.rows]);

export function resetTable() {
  tableStore.set(initialState);
}
"""

AUTH_STORE_TS = """\
import { writable } from 'svelte/store';
import type { User } from '$lib/types';

export const authStore = writable<User | null>(null);

export async function login(email: string, password: string) {
  const res = await fetch('/api/login', { method: 'POST' });
  const user = await res.json();
  authStore.set(user);
}

export async function logout() {
  authStore.set(null);
}
"""

TYPES_TS = """\
export interface User {
  id: string;
  email: string;
  role: 'admin' | 'viewer';
}

export type ButtonVariant = 'primary' | 'secondary' | 'danger';

export interface TableState {
  rows: unknown[];
  sortCol: string | null;
  page: number;
}

export enum Theme {
  Light = 'light',
  Dark = 'dark',
}
"""

PAGE_SVELTE = """\
<script lang="ts">
  import DataTable from '$lib/components/DataTable.svelte';
  import { authStore } from '$lib/stores/authStore';

  export let data: { items: Item[] };
</script>

<DataTable items={data.items} on:rowClick />
"""


# ---------------------------------------------------------------------------
# Fixtures: virtual filesystem via tmp_path
# ---------------------------------------------------------------------------

@pytest.fixture
def svelte_project(tmp_path: Path) -> Path:
    """
    Build a minimal virtual SvelteKit project on disk.
    Returns the project root (tmp_path).
    """
    # lib/components
    comp = tmp_path / "src" / "lib" / "components"
    comp.mkdir(parents=True)
    (comp / "Button.svelte").write_text(SIMPLE_BUTTON_SVELTE)
    (comp / "DataTable.svelte").write_text(DATA_TABLE_SVELTE)
    (comp / "Spinner.svelte").write_text(NO_EXPORTS_SVELTE)

    # lib/stores
    stores = tmp_path / "src" / "lib" / "stores"
    stores.mkdir(parents=True)
    (stores / "tableStore.ts").write_text(TABLE_STORE_TS)
    (stores / "authStore.ts").write_text(AUTH_STORE_TS)

    # lib/types
    lib = tmp_path / "src" / "lib"
    (lib / "types.ts").write_text(TYPES_TS)

    # routes
    routes = tmp_path / "src" / "routes"
    routes.mkdir(parents=True)
    (routes / "+layout.svelte").write_text(LAYOUT_SVELTE)
    (routes / "+page.svelte").write_text(PAGE_SVELTE)

    return tmp_path
