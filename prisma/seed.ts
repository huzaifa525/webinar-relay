import { PrismaClient } from '@prisma/client';
import crypto from 'crypto';

const prisma = new PrismaClient();

function hashPassword(password: string): string {
  return crypto.createHash('sha256').update(password).digest('hex');
}

async function main() {
  console.log('Seeding database...');

  // Create default admin
  const adminUsername = process.env.ADMIN_USERNAME || 'admin';
  const adminPassword = process.env.ADMIN_PASSWORD || 'Huzaifa5253@';

  await prisma.adminCredential.upsert({
    where: { username: adminUsername },
    update: {},
    create: {
      username: adminUsername,
      passwordHash: hashPassword(adminPassword),
    },
  });
  console.log(`Admin user "${adminUsername}" created/verified`);

  // Create default ITS webinar settings
  const itsSettingExists = await prisma.webinarSetting.findFirst();
  if (!itsSettingExists) {
    await prisma.webinarSetting.create({
      data: {
        youtubeVideoId: 'GXRL7PcPbOA',
        webinarTitle: 'Ashara Mubaraka 1447 - Ratlam Relay (ITS)',
        webinarDescription: 'Welcome to the live relay of Ashara Mubaraka 1447. This stream is authorized for ITS members only.',
        webinarDate: 'August 9-15, 2025',
        webinarTime: '7:30 AM - 12:30 PM IST',
        webinarSpeaker: 'Speaker',
        noWebinar: false,
      },
    });
    console.log('Default ITS webinar settings created');
  }

  // Create default Majlis webinar settings
  const majlisSettingExists = await prisma.majlisWebinarSetting.findFirst();
  if (!majlisSettingExists) {
    await prisma.majlisWebinarSetting.create({
      data: {
        youtubeVideoId: 'GXRL7PcPbOA',
        webinarTitle: 'Ashara Mubaraka 1447 - Ratlam Relay (Majlis)',
        webinarDescription: 'Welcome to the live relay of Ashara Mubaraka 1447. This stream is authorized for Majlis members only.',
        webinarDate: 'August 9-15, 2025',
        webinarTime: '7:30 AM - 12:30 PM IST',
        webinarSpeaker: 'Speaker',
        noWebinar: false,
      },
    });
    console.log('Default Majlis webinar settings created');
  }

  console.log('Seeding complete!');
}

main()
  .catch((e) => {
    console.error('Seeding error:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
