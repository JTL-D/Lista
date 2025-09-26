
// js/loader.js
export async function Loader(ctx) {
  const wbMaster = new ExcelJS.Workbook();
  await wbMaster.xlsx.load(await ctx.files.master.arrayBuffer());
  ctx.context.workbookMaster = wbMaster;

  const wbInfo = new ExcelJS.Workbook();
  await wbInfo.xlsx.load(await ctx.files.info.arrayBuffer());
  ctx.context.workbookInfo = wbInfo;

  return ctx;
}
