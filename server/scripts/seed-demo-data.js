/**
 * 插入示例数据，用于体验和测试
 * 使用方法: node server/scripts/seed-demo-data.js
 */
const { initDatabase, closeDatabase } = require('../database');
const { transformPendingArticles } = require('../services/transformer');

const demoArticles = [
  {
    source_name: 'Nature Medicine',
    source_url: 'https://www.nature.com/nm/',
    original_title: 'New clinical trial shows walking 30 minutes daily reduces risk of diabetes by 40%',
    original_content: 'A landmark study published in Nature Medicine involving 50,000 participants over 10 years has found that moderate walking for just 30 minutes per day can reduce the risk of developing type 2 diabetes by up to 40%. The clinical trial, conducted across 12 countries, showed that consistent moderate exercise was more effective than intermittent high-intensity workouts for blood sugar management in middle-aged and elderly adults. Researchers recommend that adults over 50 incorporate daily walking into their routine, preferably after meals. The study also found improvements in cardiovascular health markers, including lower blood pressure and improved cholesterol levels.',
    original_link: 'https://example.com/nature-walking-diabetes-1',
    category: 'fitness',
    published_at: new Date().toISOString(),
  },
  {
    source_name: 'WHO News',
    source_url: 'https://www.who.int/news',
    original_title: 'WHO releases new guidelines on hypertension management for elderly patients',
    original_content: 'The World Health Organization has updated its guidelines for managing hypertension in patients aged 60 and above. The new recommendations emphasize a combination of lifestyle modifications and medication adherence. Key findings include the importance of reducing sodium intake to less than 5 grams per day, maintaining regular physical activity of at least 150 minutes per week, and the critical role of regular blood pressure monitoring at home. The guidelines also highlight the risks of over-treatment in elderly patients and recommend personalized blood pressure targets based on individual health status. Meta-analysis of 23 peer-reviewed studies confirmed these recommendations.',
    original_link: 'https://example.com/who-hypertension-2',
    category: 'chronic_disease',
    published_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    source_name: 'Harvard Health Blog',
    source_url: 'https://www.health.harvard.edu/',
    original_title: 'Mediterranean diet linked to 30% lower risk of Alzheimer disease in new research',
    original_content: 'Harvard researchers have published findings showing that adherence to a Mediterranean diet rich in olive oil, nuts, fish, and vegetables is associated with a 30% reduction in Alzheimer disease risk. The study followed 12,000 adults aged 55-80 over 15 years. Participants who closely followed the Mediterranean eating pattern showed better cognitive test scores and less brain atrophy on MRI scans. The diet is high in omega-3 fatty acids, antioxidants, and fiber, all of which have neuroprotective properties. Researchers suggest that the anti-inflammatory effects of the diet may protect against neurodegeneration. These findings were peer-reviewed and published in The Lancet Neurology.',
    original_link: 'https://example.com/harvard-alzheimer-diet-3',
    category: 'nutrition',
    published_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    source_name: 'Medical News Today',
    source_url: 'https://www.medicalnewstoday.com/',
    original_title: 'Tai chi practice shown to improve balance and prevent falls in seniors over 65',
    original_content: 'A systematic review of 28 randomized controlled trials has confirmed that regular tai chi practice significantly reduces the risk of falls in adults over 65. The analysis, which included data from over 7,000 participants, found that practicing tai chi for 60 minutes twice a week for at least 12 weeks reduced fall risk by 43%. Tai chi improves balance, leg strength, and proprioception. It also provides mental health benefits including reduced anxiety and improved sleep quality. Physical therapists recommend tai chi as a safe, low-impact exercise suitable for elderly individuals with varying fitness levels. The practice also showed benefits for managing chronic pain and improving flexibility.',
    original_link: 'https://example.com/taichi-falls-4',
    category: 'elderly_care',
    published_at: new Date(Date.now() - 10800000).toISOString(),
  },
  {
    source_name: 'NIH Research Matters',
    source_url: 'https://www.nih.gov/',
    original_title: 'Study finds strong link between sleep quality and cardiovascular health in middle-aged adults',
    original_content: 'Researchers at the National Institutes of Health have found compelling evidence linking poor sleep quality to increased cardiovascular disease risk in adults aged 45-65. The study of 20,000 participants revealed that those sleeping less than 6 hours per night had a 27% higher risk of heart disease. The research also identified that sleep disorders like insomnia and sleep apnea contribute to higher blood pressure, increased inflammation markers, and impaired glucose metabolism. Scientists recommend maintaining consistent sleep schedules, creating dark and quiet sleeping environments, and limiting screen time before bed. Cognitive behavioral therapy for insomnia was found more effective than sleeping pills for long-term improvement.',
    original_link: 'https://example.com/nih-sleep-heart-5',
    category: 'mental_health',
    published_at: new Date(Date.now() - 14400000).toISOString(),
  },
  {
    source_name: 'ScienceDaily Health',
    source_url: 'https://www.sciencedaily.com/',
    original_title: 'Breakthrough: New blood test can detect early-stage cancer with 90% accuracy',
    original_content: 'Scientists have developed a revolutionary blood test that can detect multiple types of cancer at early stages with approximately 90% accuracy. The test, known as a liquid biopsy, analyzes circulating tumor DNA fragments in the blood. Early clinical trials involving 6,000 patients showed that the test could identify lung, colorectal, pancreatic, and liver cancers up to four years before conventional diagnosis methods. The screening is particularly valuable for people over 50 who are at higher risk for these cancers. Researchers at Johns Hopkins University led the study, which was published in the journal Science. The test is expected to become available for routine screening within the next few years pending regulatory approval.',
    original_link: 'https://example.com/science-blood-cancer-6',
    category: 'medical_research',
    published_at: new Date(Date.now() - 18000000).toISOString(),
  },
  {
    source_name: 'WebMD Health',
    source_url: 'https://www.webmd.com/',
    original_title: 'Five foods that naturally lower blood sugar levels according to nutrition experts',
    original_content: 'Nutrition experts have identified five key foods that can help manage blood sugar levels naturally. Bitter melon, cinnamon, leafy green vegetables, whole grains, and legumes have all shown significant effects in clinical studies. A diet rich in these foods, combined with regular exercise, can reduce HbA1c levels by up to 1.5% in people with prediabetes. Fiber-rich foods slow glucose absorption, while cinnamon has been shown to improve insulin sensitivity. Experts recommend eating balanced meals with protein and fiber at every sitting, avoiding processed sugars, and monitoring portion sizes. These dietary changes are particularly beneficial for adults managing type 2 diabetes or metabolic syndrome.',
    original_link: 'https://example.com/webmd-blood-sugar-food-7',
    category: 'nutrition',
    published_at: new Date(Date.now() - 21600000).toISOString(),
  },
  {
    source_name: 'The Lancet',
    source_url: 'https://www.thelancet.com/',
    original_title: 'Large-scale study reveals benefits of traditional Chinese medicine combined with modern treatment for chronic pain',
    original_content: 'A comprehensive study published in The Lancet has found that integrating traditional Chinese medicine techniques such as acupuncture and herbal remedies with conventional medical treatment provides superior outcomes for chronic pain management. The randomized controlled trial of 8,500 patients with chronic lower back pain and osteoarthritis showed that the combined approach reduced pain scores by 35% compared to 22% with conventional treatment alone. The study was conducted at 15 hospitals across China and followed strict peer-reviewed scientific protocols. Researchers noted that acupuncture was particularly effective for older patients who could not tolerate high doses of painkillers. Traditional Chinese herbal formulas containing turmeric and ginger also showed anti-inflammatory properties.',
    original_link: 'https://example.com/lancet-tcm-pain-8',
    category: 'traditional_medicine',
    published_at: new Date(Date.now() - 25200000).toISOString(),
  },
  {
    source_name: 'Harvard Health Blog',
    source_url: 'https://www.health.harvard.edu/',
    original_title: 'Regular social activities may reduce risk of dementia by 26% in elderly adults',
    original_content: 'New research from Harvard Medical School suggests that elderly adults who maintain active social lives have a 26% lower risk of developing dementia. The prospective cohort study tracked 15,000 adults aged 60 and above for 12 years. Activities such as joining community groups, volunteering, playing board games with friends, and regular family gatherings were associated with better cognitive function and slower brain aging. Social isolation, on the other hand, was linked to increased inflammation and faster cognitive decline. The researchers recommend that healthcare providers screen for social isolation as a risk factor for cognitive impairment. The findings were published in JAMA Neurology.',
    original_link: 'https://example.com/harvard-social-dementia-9',
    category: 'elderly_care',
    published_at: new Date(Date.now() - 28800000).toISOString(),
  },
  {
    source_name: 'Nature Medicine',
    source_url: 'https://www.nature.com/nm/',
    original_title: 'Vitamin D supplementation reduces risk of respiratory infections in elderly by 25%',
    original_content: 'A large meta-analysis published in Nature Medicine has confirmed that daily vitamin D supplementation of 1000-2000 IU can reduce the risk of acute respiratory infections by 25% in adults over 60. The analysis combined data from 42 randomized controlled trials involving over 40,000 participants worldwide. The protective effect was strongest in individuals who were vitamin D deficient at baseline. Researchers also found that daily or weekly supplementation was more effective than large monthly doses. In addition to respiratory benefits, adequate vitamin D levels were associated with better bone health, reduced fall risk, and improved immune function. The WHO and NIH both recommend regular vitamin D screening for elderly adults.',
    original_link: 'https://example.com/nature-vitd-respiratory-10',
    category: 'disease_prevention',
    published_at: new Date(Date.now() - 32400000).toISOString(),
  },
  {
    source_name: 'Medical News Today',
    source_url: 'https://www.medicalnewstoday.com/',
    original_title: 'New research: Managing stress through meditation lowers blood pressure as effectively as medication',
    original_content: 'A groundbreaking study has demonstrated that mindfulness meditation practiced for 20 minutes daily can lower systolic blood pressure by an average of 12 mmHg, comparable to the effects of first-line antihypertensive medications. The clinical trial enrolled 1,200 adults with stage 1 hypertension and followed them for two years. The meditation group also showed reduced cortisol levels, improved heart rate variability, and better emotional well-being. Researchers from Johns Hopkins University noted that meditation activates the parasympathetic nervous system, counteracting the stress response that contributes to high blood pressure. The study was published in the Journal of the American Heart Association and represents peer-reviewed evidence supporting mind-body interventions.',
    original_link: 'https://example.com/meditation-bp-11',
    category: 'mental_health',
    published_at: new Date(Date.now() - 36000000).toISOString(),
  },
  {
    source_name: 'WHO News',
    source_url: 'https://www.who.int/news',
    original_title: 'Global report: Physical rehabilitation programs significantly improve quality of life after stroke',
    original_content: 'A new WHO global report highlights the importance of early and sustained physical rehabilitation for stroke survivors. Data from 50 countries show that patients who begin rehabilitation within the first two weeks post-stroke have 40% better functional outcomes at one year. The report recommends a multidisciplinary approach including physical therapy, occupational therapy, and speech therapy. For elderly stroke survivors, home-based rehabilitation programs were found to be as effective as hospital-based programs when properly supervised. The report also emphasizes the role of family caregivers and recommends training programs for them. Regular follow-up assessments and individualized rehabilitation plans were identified as key success factors.',
    original_link: 'https://example.com/who-stroke-rehab-12',
    category: 'rehabilitation',
    published_at: new Date(Date.now() - 39600000).toISOString(),
  },
];

async function main() {
  console.log('正在插入示例数据...\n');

  await initDatabase();

  const db = require('../database').getDatabase();

  const insertStmt = db.prepare(`
    INSERT OR IGNORE INTO articles
      (source_name, source_url, original_title, original_content, original_link,
       original_language, category, published_at, status)
    VALUES
      (@source_name, @source_url, @original_title, @original_content, @original_link,
       @original_language, @category, @published_at, 'pending')
  `);

  let added = 0;
  for (const article of demoArticles) {
    const result = insertStmt.run({
      ...article,
      original_language: 'en',
    });
    if (result.changes > 0) {
      added++;
    }
  }

  console.log(`插入了 ${added} 篇示例文章\n`);

  // 转换文章（翻译 + 评估可信度 + 提取要点）
  console.log('正在转换文章（翻译、评估可信度、提取要点）...\n');
  transformPendingArticles();

  console.log('\n示例数据加载完成！启动服务后即可在浏览器中查看。');
  closeDatabase();
}

main();
