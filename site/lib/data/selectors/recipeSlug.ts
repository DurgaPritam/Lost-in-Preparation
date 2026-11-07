/** Recipe ids contain ':' and '#'; the page slug replaces them with '_' (unique: checked when pages are built). */
export const recipeSlug = (id: string) => id.replace(/[:#]/g, '_');
