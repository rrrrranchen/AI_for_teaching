<template>
  <div class="public-knowledge-bases-container">
    <div class="header">
      <h2>共享知识库</h2>
      <div class="search-bar">
        <a-tabs v-model:activeKey="activeTab" @change="handleTabChange">
          <a-tab-pane key="list" tab="列表浏览"></a-tab-pane>
          <a-tab-pane key="search" tab="模糊搜索"></a-tab-pane>
          <a-tab-pane key="deep" tab="深度搜索"></a-tab-pane>
        </a-tabs>

        <div v-if="activeTab === 'list'" class="filter-controls">
          <a-input-search
            v-model:value="listParams.keyword"
            placeholder="搜索知识库名称"
            style="width: 240px"
            @search="fetchPublicKnowledgeBases"
            allow-clear
          />
          <a-select
            v-model:value="listParams.sort_by"
            placeholder="排序方式"
            style="width: 120px; margin-left: 8px"
          >
            <a-select-option value="name">名称</a-select-option>
            <a-select-option value="created_at">创建时间</a-select-option>
            <a-select-option value="updated_at">更新时间</a-select-option>
            <a-select-option value="usage_count">使用次数</a-select-option>
          </a-select>
          <a-select
            v-model:value="listParams.order"
            placeholder="排序顺序"
            style="width: 100px; margin-left: 8px"
          >
            <a-select-option value="asc">升序</a-select-option>
            <a-select-option value="desc">降序</a-select-option>
          </a-select>
          <a-select
            v-model:value="listParams.base_type"
            placeholder="知识库类型"
            style="width: 120px; margin-left: 8px"
            allow-clear
          >
            <a-select-option value="structural">结构化</a-select-option>
            <a-select-option value="non_structural">非结构化</a-select-option>
          </a-select>
          <a-button
            type="primary"
            @click="fetchPublicKnowledgeBases"
            style="margin-left: 8px"
          >
            <template #icon><search-outlined /></template>
            搜索
          </a-button>
          <a-button @click="resetListSearch" style="margin-left: 8px">
            <template #icon><redo-outlined /></template>
            重置
          </a-button>
        </div>

        <div v-if="activeTab === 'search'" class="search-controls">
          <a-input-search
            v-model:value="searchParams.keyword"
            placeholder="输入关键词搜索"
            style="width: 300px"
            @search="handleSearch"
            allow-clear
          />
          <a-button
            type="primary"
            @click="handleSearch"
            style="margin-left: 8px"
          >
            <template #icon><search-outlined /></template>
            搜索
          </a-button>
        </div>

        <div v-if="activeTab === 'deep'" class="deep-search-controls">
          <a-input-search
            v-model:value="deepSearchParams.keyword"
            placeholder="输入关键词深度搜索内容"
            style="width: 300px"
            @search="handleDeepSearch"
            allow-clear
          />
          <a-input-number
            v-model:value="deepSearchParams.similarity"
            placeholder="相似度"
            :min="0.1"
            :max="1"
            :step="0.1"
            style="width: 100px; margin-left: 8px"
          />
          <a-input-number
            v-model:value="deepSearchParams.chunk_count"
            placeholder="返回数量"
            :min="1"
            :max="20"
            style="width: 100px; margin-left: 8px"
          />
          <a-button
            type="primary"
            @click="handleDeepSearch"
            style="margin-left: 8px"
          >
            <template #icon><search-outlined /></template>
            深度搜索
          </a-button>
        </div>
      </div>
    </div>

    <a-alert
      message="共享知识库使用说明"
      description="您可以浏览和搜索其他用户公开分享的知识库，并将其迁移到自己的知识库中使用"
      type="info"
      show-icon
      style="margin-bottom: 16px"
    />

    <!-- 列表浏览模式 -->
    <div v-if="activeTab === 'list'">
      <a-list
        :data-source="publicKnowledgeBases"
        :loading="loading"
        :pagination="pagination"
        item-layout="vertical"
        bordered
      >
        <template #renderItem="{ item }">
          <a-list-item style="margin-bottom: 8px; background-color: #f6f6f6">
            <template #actions>
              <span>
                <folder-outlined />
                {{ item.categories.length }} 个类目
              </span>
              <span>
                <user-outlined />
                {{ item.author_name || "未知作者" }}
              </span>
              <span>
                <clock-circle-outlined />
                {{ formatDate(item.created_at) }}
              </span>
              <span>
                <star-outlined />
                使用次数: {{ item.usage_count || 0 }}
              </span>
              <a-tag
                :color="item.base_type === 'structural' ? 'blue' : 'purple'"
              >
                {{ item.base_type === "structural" ? "结构化" : "非结构化" }}
              </a-tag>
              <a-button
                type="primary"
                size="small"
                @click="handleMigrate(item.id)"
                :loading="migratingId === item.id"
              >
                <template #icon><download-outlined /></template>
                迁移到我的知识库
              </a-button>
            </template>

            <a-list-item-meta>
              <template #title>
                <a style="font-size: large; margin-right: 8px">{{
                  item.name
                }}</a>
              </template>
              <template #description>
                {{ item.description || "暂无描述" }}
              </template>
            </a-list-item-meta>

            <div class="kb-categories" v-if="item.categories.length > 0">
              <h4>关联类目:</h4>
              <div class="category-tags">
                <a-tag
                  v-for="cat in item.categories"
                  :key="cat.id"
                  :color="cat.type === 'structural' ? 'blue' : 'purple'"
                >
                  {{ cat.name }}
                </a-tag>
              </div>
            </div>
          </a-list-item>
        </template>
      </a-list>
    </div>

    <!-- 模糊搜索结果 -->
    <div v-if="activeTab === 'search'">
      <a-list
        :data-source="searchResults"
        :loading="searchLoading"
        :pagination="searchPagination"
        item-layout="vertical"
        bordered
      >
        <template #renderItem="{ item }">
          <a-list-item style="margin-bottom: 8px">
            <template #actions>
              <span>
                <user-outlined />
                {{ item.author_name }}
              </span>
              <span>
                <clock-circle-outlined />
                {{ formatDate(item.created_at) }}
              </span>
              <a-tag :color="getMatchTagColor(item.match_type)">
                {{ item.match_type }}
              </a-tag>
              <a-button
                type="primary"
                size="small"
                @click="handleMigrate(item.id)"
                :loading="migratingId === item.id"
              >
                <template #icon><download-outlined /></template>
                迁移到我的知识库
              </a-button>
            </template>

            <a-list-item-meta>
              <template #title>
                <a style="font-size: large; margin-right: 8px">{{
                  item.name
                }}</a>
                <a-tag
                  :color="item.base_type === 'structural' ? 'blue' : 'purple'"
                >
                  {{ item.base_type === "structural" ? "结构化" : "非结构化" }}
                </a-tag>
              </template>
              <template #description>
                <div
                  v-html="
                    highlightKeyword(item.description, searchParams.keyword)
                  "
                ></div>
              </template>
            </a-list-item-meta>

            <div class="kb-categories" v-if="item.categories.length > 0">
              <h4>关联类目:</h4>
              <div class="category-tags">
                <a-tag
                  v-for="cat in item.categories"
                  :key="cat.id"
                  :color="cat.type === 'structural' ? 'blue' : 'purple'"
                >
                  {{ cat.name }}
                </a-tag>
              </div>
            </div>
          </a-list-item>
        </template>

        <template #footer>
          <div class="search-meta">
            <span>共找到 {{ searchMeta.total_matches }} 个结果</span>
            <span style="margin-left: 16px">
              名称匹配: {{ searchMeta.name_matches }} 个
            </span>
            <span style="margin-left: 16px">
              描述匹配: {{ searchMeta.desc_matches }} 个
            </span>
          </div>
        </template>
      </a-list>
    </div>

    <!-- 深度搜索结果 -->
    <div v-if="activeTab === 'deep'">
      <a-list
        :data-source="deepSearchResults"
        :loading="deepSearchLoading"
        item-layout="vertical"
        bordered
      >
        <template #renderItem="{ item }">
          <a-list-item style="margin-bottom: 8px">
            <template #actions>
              <span>
                <user-outlined />
                {{ item.knowledge_base.author_name }}
              </span>
              <a-tag :color="getScoreTagColor(item.score)">
                相似度: {{ (item.score * 100).toFixed(1) }}%
              </a-tag>
              <a-button
                type="primary"
                size="small"
                @click="handleMigrate(item.knowledge_base.id)"
                :loading="migratingId === item.knowledge_base.id"
              >
                <template #icon><download-outlined /></template>
                迁移到我的知识库
              </a-button>
            </template>

            <a-list-item-meta>
              <template #title>
                <a style="font-size: large; margin-right: 8px">
                  {{ item.knowledge_base.name }}
                </a>
                <a-tag>来自: {{ item.knowledge_base.author_name }}</a-tag>
              </template>
              <template #description>
                <div class="deep-search-result">
                  <h4>匹配内容:</h4>
                  <div
                    class="matched-text"
                    v-html="
                      highlightKeyword(item.text, deepSearchParams.keyword)
                    "
                  ></div>
                  <div class="source-info">
                    <span>
                      <folder-outlined />
                      {{ item.category }}
                    </span>
                    <span style="margin-left: 8px">
                      <file-outlined />
                      {{ item.file }}
                    </span>
                  </div>
                </div>
              </template>
            </a-list-item-meta>
          </a-list-item>
        </template>

        <template #footer>
          <div class="search-meta">
            <span>共找到 {{ deepSearchMeta.matches }} 个匹配内容</span>
          </div>
        </template>
      </a-list>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from "vue";
import { message } from "ant-design-vue";
import {
  SearchOutlined,
  RedoOutlined,
  FolderOutlined,
  UserOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  StarOutlined,
  FileOutlined,
} from "@ant-design/icons-vue";
import {
  migratePublicKnowledgeBase,
  getPublicKnowledgeBases,
  searchPublicKnowledgeBases,
  deepSearchPublicKnowledgeBases,
} from "@/api/knowledgebase";

interface ListParams {
  sort_by?: "name" | "created_at" | "updated_at" | "usage_count";
  order?: "asc" | "desc";
  category_id?: number;
  base_type?: "structural" | "non_structural";
  min_usage?: number;
  keyword?: string;
  page?: number;
  per_page?: number;
}

interface SearchParams {
  keyword: string;
  page?: number;
  per_page?: number;
}

interface DeepSearchParams {
  keyword: string;
  kb_ids?: string;
  similarity?: number;
  chunk_count?: number;
  data_type?: string;
}

const activeTab = ref<"list" | "search" | "deep">("list");
const loading = ref(false);
const searchLoading = ref(false);
const deepSearchLoading = ref(false);
const migratingId = ref<number | null>(null);

const publicKnowledgeBases = ref<any[]>([]);
const searchResults = ref<any[]>([]);
const deepSearchResults = ref<any[]>([]);

const listParams = reactive<ListParams>({
  keyword: undefined,
  sort_by: "updated_at",
  order: "desc",
  base_type: undefined,
  page: 1,
  per_page: 10,
});

const searchParams = reactive<SearchParams>({
  keyword: "",
  page: 1,
  per_page: 10,
});

const deepSearchParams = reactive<DeepSearchParams>({
  keyword: "",
  similarity: 0.7,
  chunk_count: 5,
});

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  onChange: (page: number, pageSize: number) => {
    listParams.page = page;
    listParams.per_page = pageSize;
    fetchPublicKnowledgeBases();
  },
});

const searchPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  onChange: (page: number, pageSize: number) => {
    searchParams.page = page;
    searchParams.per_page = pageSize;
    handleSearch();
  },
});

const searchMeta = reactive({
  total_matches: 0,
  name_matches: 0,
  desc_matches: 0,
});

const deepSearchMeta = reactive({
  matches: 0,
});

onMounted(() => {
  fetchPublicKnowledgeBases();
});

const fetchPublicKnowledgeBases = async () => {
  loading.value = true;
  try {
    const result = await getPublicKnowledgeBases(listParams);
    publicKnowledgeBases.value = result.knowledge_bases;
    pagination.total = result.count;
    pagination.current = listParams.page || 1;
    pagination.pageSize = listParams.per_page || 10;
  } catch (error) {
    message.error("获取公共知识库列表失败");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const handleSearch = async () => {
  if (!searchParams.keyword.trim()) {
    message.warning("请输入搜索关键词");
    return;
  }

  searchLoading.value = true;
  try {
    const result = await searchPublicKnowledgeBases(
      searchParams.keyword,
      searchParams.page,
      searchParams.per_page
    );

    searchResults.value = result.results;
    searchMeta.total_matches = result.pagination.total;
    searchMeta.name_matches = result.search_meta.name_matches;
    searchMeta.desc_matches = result.search_meta.desc_matches;

    searchPagination.total = result.pagination.total;
    searchPagination.current = result.pagination.current_page;
    searchPagination.pageSize = result.pagination.per_page;
  } catch (error) {
    message.error("搜索公开知识库失败");
    console.error(error);
  } finally {
    searchLoading.value = false;
  }
};

const handleDeepSearch = async () => {
  if (!deepSearchParams.keyword.trim()) {
    message.warning("请输入搜索关键词");
    return;
  }

  deepSearchLoading.value = true;
  try {
    const result = await deepSearchPublicKnowledgeBases({
      keyword: deepSearchParams.keyword,
      similarity: deepSearchParams.similarity,
      chunk_count: deepSearchParams.chunk_count,
    });

    deepSearchResults.value = result.results;
    deepSearchMeta.matches = result.matches;
  } catch (error) {
    message.error("深度搜索失败");
    console.error(error);
  } finally {
    deepSearchLoading.value = false;
  }
};

const handleMigrate = async (kbId: number) => {
  migratingId.value = kbId;
  try {
    const result = await migratePublicKnowledgeBase(kbId);
    message.success(
      `迁移成功！新知识库: ${result.data.new_knowledge_base.name}`
    );
    // 如果是列表模式，刷新列表
    if (activeTab.value === "list") {
      fetchPublicKnowledgeBases();
    }
  } catch (error) {
    message.error("迁移知识库失败");
    console.error(error);
  } finally {
    migratingId.value = null;
  }
};

const handleTabChange = (key: string) => {
  activeTab.value = key as "list" | "search" | "deep";
  // 切换到搜索标签时重置搜索参数
  if (activeTab.value === "search") {
    searchParams.keyword = "";
    searchResults.value = [];
  } else if (activeTab.value === "deep") {
    deepSearchParams.keyword = "";
    deepSearchResults.value = [];
  }
};

const resetListSearch = () => {
  listParams.keyword = undefined;
  listParams.base_type = undefined;
  listParams.page = 1;
  fetchPublicKnowledgeBases();
};

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString();
};

const getMatchTagColor = (matchType: string) => {
  return matchType === "名称匹配" ? "green" : "blue";
};

const getScoreTagColor = (score: number) => {
  if (score >= 0.9) return "green";
  if (score >= 0.7) return "blue";
  if (score >= 0.5) return "orange";
  return "red";
};

const highlightKeyword = (text: string | undefined, keyword: string) => {
  if (!text || !keyword) return text || "";
  const regex = new RegExp(keyword, "gi");
  return text.replace(
    regex,
    (match) =>
      `<span style="background-color: yellow; font-weight: bold;">${match}</span>`
  );
};
</script>

<style scoped>
.public-knowledge-bases-container {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
}
.header {
  display: flex;
  flex-direction: column;
  margin-bottom: 16px;
}
.search-bar {
  margin-top: 16px;
}
.filter-controls,
.search-controls,
.deep-search-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.kb-categories {
  margin-top: 12px;
}
.kb-categories h4 {
  margin-bottom: 8px;
  font-weight: 500;
}
.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.search-meta {
  margin-top: 16px;
  color: #666;
  font-size: 14px;
}
.deep-search-result {
  margin-top: 8px;
}
.matched-text {
  background-color: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  margin: 8px 0;
}
.source-info {
  color: #666;
  font-size: 14px;
}
</style>
